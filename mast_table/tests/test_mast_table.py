from mast_table.base import BaseMastTable, col_unique_row_index, serialize
import numpy as np
import astropy.units as u
from astropy.table import Table
from jdaviz.core.marks import FootprintOverlay
from mast_aladin.app import MastAladin


def footprint_marks(jdaviz_app):
    """Footprint overlays currently drawn in the jdaviz image viewer."""
    glue_viewer = jdaviz_app.viewers['Image']._obj.glue_viewer
    return [
        mark for mark in glue_viewer.figure.marks
        if isinstance(mark, FootprintOverlay)
    ]


def test_mast_table_init(mast_observation_table):
    mast_table = BaseMastTable(mast_observation_table)

    # check that astropy table is stored on the widget
    assert 's_region' in mast_table.table.colnames

    # check that s_region col exists in available widget columns
    assert 's_region' in mast_table.headers_avail

    # check that s_region col isn't visible by default
    assert 's_region' not in mast_table.headers_visible

    # the MAST observation query has a ArchiveFileID column,
    # which should be chosen as the default item_key:
    assert mast_table.item_key == 'ArchiveFileID'


def test_fileset_results_enable_viewer_buttons(mast_observation_table):
    mast_table = BaseMastTable(mast_observation_table)

    # a fileset query result is recognized from its columns, and its
    # footprints can be sent to either viewer
    assert mast_table.mission == 'jwst'
    assert mast_table.enable_load_in_app


def test_product_list_results_enable_viewer_buttons():
    products = Table({
        'product_key': ['product-1'],
        'filename': ['jw_product_cal.fits'],
    })
    mast_table = BaseMastTable(products)

    assert mast_table.mission == 'list_products'
    assert mast_table.enable_load_in_app


def test_selected_s_regions_splits_rows_with_several_shapes():
    first = 'POLYGON ICRS 9.99 19.99 10.01 19.99 10.01 20.01'
    second = 'POLYGON ICRS 9.98 19.98 10.00 19.98 10.00 20.00'
    table = Table({
        'fileSetName': ['compound', 'blank'],
        # MAST may return several shapes in a single s_region value
        's_region': [f'{first}  {second}', '  '],
    })
    mast_table = BaseMastTable(table)
    mast_table.selected_rows = ['0', '1']

    # each shape is sent separately, and blank values are skipped
    assert mast_table._selected_s_regions() == [first, second]


def test_selected_rows_follow_the_click(mast_observation_table):
    file_set_names = list(mast_observation_table['fileSetName'])
    mast_table = BaseMastTable(mast_observation_table)
    mast_table.selected_rows = ['0']

    # the buttons send the current frontend selection along with the click,
    # which can still be ahead of the synced traitlet
    from_click = mast_table._selected_rows_table_from_args((['1', '2'],))
    assert list(from_click['fileSetName']) == file_set_names[1:3]

    # calls from the API fall back to the synced traitlet
    from_traitlet = mast_table._selected_rows_table_from_args(())
    assert list(from_traitlet['fileSetName']) == file_set_names[:1]


def test_selected_fileset_rows_shown_in_jdaviz(jdaviz_app, mast_observation_table):
    mast_table = BaseMastTable(mast_observation_table)
    footprints = jdaviz_app.plugins['Footprints']

    assert mast_table.vue_open_selected_rows_in_jdaviz(['0', '1']) is jdaviz_app

    # footprints can only be drawn when aligned by WCS
    assert jdaviz_app.plugins['Orientation'].align_by.selected == 'WCS'

    # the selection replaces the preset footprints jdaviz starts with
    assert footprints.overlay.choices == ['mast-table selection']
    assert len(footprints.overlay_regions) == 2
    assert [mark.visible for mark in footprint_marks(jdaviz_app)] == [True, True]

    # clicking again replaces the overlay with the current selection
    assert mast_table.vue_open_selected_rows_in_jdaviz(['2']) is jdaviz_app

    assert footprints.overlay.choices == ['mast-table selection']
    assert len(footprints.overlay_regions) == 1
    assert [mark.visible for mark in footprint_marks(jdaviz_app)] == [True]


def test_selected_fileset_rows_shown_in_aladin(mast_observation_table):
    aladin = MastAladin()
    mast_table = BaseMastTable(mast_observation_table)

    assert mast_table.vue_open_selected_rows_in_aladin(['0', '1']) is aladin
    first_overlay = mast_table._aladin_fileset_overlay
    assert first_overlay.name == 'mast-table selection'

    # clicking again replaces the overlay with the current selection
    assert mast_table.vue_open_selected_rows_in_aladin(['2']) is aladin
    assert mast_table._aladin_fileset_overlay is not first_overlay
    assert mast_table._aladin_fileset_overlay.name == 'mast-table selection'


def test_server_side_pagination(mast_observation_table):
    # fixture has 5 rows
    n_rows = len(mast_observation_table)
    mast_table = BaseMastTable(mast_observation_table, items_per_page=2)

    # the row cache now holds a reference to the astropy Table (no upfront
    # whole-table serialization); only the first page is pushed to the UI
    assert mast_table.server_pagination is True
    assert mast_table.server_items_length == n_rows
    assert mast_table._all_items is mast_table.table
    assert len(mast_table._all_items) == n_rows
    assert len(mast_table.items) == min(2, n_rows)

    # simulate the frontend updating page/itemsPerPage and verify the slice updates
    mast_table.table_options = {'page': 2, 'itemsPerPage': 2}
    assert len(mast_table.items) == min(2, max(0, n_rows - 2))
    # the first row of page 2 should correspond to the third row of the cache
    assert (
        mast_table.items[0][col_unique_row_index]
        == str(mast_table._all_items[col_unique_row_index][2])
    )

    # itemsPerPage = -1 means "show all"
    mast_table.table_options = {'page': 1, 'itemsPerPage': -1}
    assert len(mast_table.items) == n_rows


def test_server_side_pagination_disabled(mast_observation_table):
    mast_table = BaseMastTable(mast_observation_table, server_pagination=False)
    # verify the kwarg actually reached the traitlet
    assert mast_table.server_pagination is False
    # with server pagination disabled, the full table is pushed to the UI
    assert len(mast_table.items) == len(mast_observation_table)


def test_serialize_respects_column_format():
    """``Column.info.format`` should drive per-column print precision."""
    t = Table({
        'ra': [12.345678, 98.765432],
        'flux': [1.2345e-15, 6.7890e-14],
        'name': ['a', 'b'],
    })
    t['ra'].info.format = '.3f'
    t['flux'].info.format = '%.2e'

    rows = serialize(t)
    assert rows[0]['ra'] == '12.346'
    assert rows[1]['ra'] == '98.765'
    assert rows[0]['flux'] == '1.23e-15'
    # columns without a format should pass through to plain Python types
    assert rows[0]['name'] == 'a'

    # NaN cells should render as an empty string when a format is set
    t2 = Table({'x': [np.nan, 1.0]})
    t2['x'].info.format = '.3f'
    rows2 = serialize(t2)
    assert rows2[0]['x'] == ''
    assert rows2[1]['x'] == '1.000'

    # Quantity columns respect the format spec (units appear in header, not cells)
    t3 = Table({'wave': [500.123, 600.456] * u.nm})
    t3['wave'].info.format = '.1f'
    rows3 = serialize(t3)
    assert rows3[0]['wave'] == '500.1'
    assert rows3[1]['wave'] == '600.5'


def test_column_format_propagates_to_widget(mast_observation_table):
    """Setting ``Column.info.format`` before constructing the widget should
    show up in the items pushed to the UI."""
    col = next(
        (c for c in mast_observation_table.colnames
         if mast_observation_table[c].dtype.kind == 'f'),
        None,
    )
    assert col is not None
    mast_observation_table[col].info.format = '.2f'
    # request "All" so the whole (small) fixture is serialized to ``items``
    mast_table = BaseMastTable(
        mast_observation_table,
        items_per_page=len(mast_observation_table),
    )
    # every visible row should have the formatted (string) value for this column
    for row in mast_table.items:
        value = row[col]
        # NaNs become '' otherwise we expect a formatted string with 2 decimals
        assert value == '' or (isinstance(value, str) and value.count('.') == 1
                               and len(value.split('.')[1]) == 2)
