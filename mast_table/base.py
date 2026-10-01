import os
import re
import warnings

from traitlets import List, Unicode, Bool, Int, Dict, observe
from ipyvuetify import VuetifyTemplate

import numpy as np
import astropy.units as u
from astropy.coordinates import SkyCoord
import jdaviz as jd
from jdaviz.core.region_translators import stcs_string2region
from regions import Regions

from mast_table import validate
from astroquery.mast import MastMissions

__all__ = [
    'BaseMastTable',
]


col_unique_row_index = '_unique_row_index'


mission_mast_ra_dec_colnames = dict(
    hst=['sci_ra', 'sci_dec'],
    roman=['ra', 'dec'],
    jwst=['targ_ra', 'targ_dec'],
    list_products=['', ''],
)


known_unique_mast_table_cols = [
    'fileSetName',  # data products from astroquery.mast.MastMissions
    'source_id',    # Gaia
    'MatchID',      # Hubble Source Catalog
    'objID',        # PanSTARRS,
    'product_key',  # list_products queries
    'obs_id',       # astroquery.mast.Observations,
    'sci_data_set_name',  # HST
]


def serialize(table):
    """
    Convert an astropy table to a list of dictionaries of JSON-safe values.

    Per-column print precision is taken from each column's
    ``Column.info.format`` attribute, so users can configure precision via
    standard astropy machinery, e.g.::

        table['flux'].info.format = '.3e'
        table['ra'].info.format = '%.5f'
    """
    column_names = table.colnames

    def replace_nan(value):
        if value.strip().lower() == 'nan':
            value = ''
        return value

    def nan_to_empty_str(column):
        nans_found = re.findall('nan', ''.join(column))
        if len(nans_found):
            column = [replace_nan(row) for row in column]
        return column

    formatted_columns = []

    for col in column_names:
        if col == col_unique_row_index or table[col].dtype.kind in ("U", "S"):
            values = [str(value) for value in table[col]]
        else:
            values = table[col].pformat(
                show_name=False,
                show_unit=False,
            )

        values = nan_to_empty_str(values)
        formatted_columns.append(values)

    formatted_rows = zip(*formatted_columns)

    serialized = [
        {name: f"{val}" for name, val in zip(column_names, row)}
        for row in formatted_rows
    ]

    return serialized


class BaseMastTable(VuetifyTemplate):
    """
    Base table widget for queries from MAST.
    """
    template_file = __file__, "base.vue"

    items = List().tag(sync=True)
    headers = List().tag(sync=True)
    headers_visible = List().tag(sync=True)
    headers_avail = List().tag(sync=True)
    show_if_empty = Bool(True).tag(sync=True)
    show_rowselect = Bool(True).tag(sync=True)
    selected_rows = List().tag(sync=True)
    show_tooltips = Bool(True).tag(sync=True)
    menu_open = Bool(False).tag(sync=True)
    enable_load_in_app = Bool(False).tag(sync=True)
    mission = Unicode(allow_none=True).tag(sync=True)
    filter_tray_open = Bool(False).tag(sync=True)
    # pagination traitlets
    items_per_page = Int(10).tag(sync=True)
    server_pagination = Bool(True).tag(sync=True)
    server_items_length = Int(0).tag(sync=True)
    table_options = Dict({}).tag(sync=True)
    sort_by = List([]).tag(sync=True)

    # item_key is a column of the table with unique values
    # for each row, enabling selection of the row by lookup
    item_key = Unicode().tag(sync=True)

    table = None
    row_select_callbacks = []

    def __init__(
        self,
        table,
        app=None,
        update_viewport=True,
        unique_column=None,
        ra_column=None,
        dec_column=None,
        **kwargs
    ):
        """
        Parameters
        ----------
        table : `~astropy.table.Table`
            A table to load.

        app : `~mast_aladin.app.MastAladin`
            An instance of the ``MastAladin`` app.

        update_viewport : bool (optional, default is `True`)
            If `True`, set the `~mast_aladin.app.MastAladin`
            viewport center to the position of the item in the
            first row of the table on load.

        unique_column : str (optional, default is `None`)
            A column which contains unique values in each row.

            If no `unique_column` is given, ``MastTable`` will look for a
            column known to have unique values for each row in common MAST
            observation queries. If no known `unique_column` is found,
            search through the table to find a column with unique rows.

            For tables with many rows, unique column searches are inefficient
            and a warning will be raised.

        ra_column : str (optional, default is `None`)
            Column name for the right ascension in degrees.

        dec_column : str (optional, default is `None`)
            Column name for the declination in degrees.

        **kwargs
            Remaining keyword arguments are passed to
            ``ipyvuetify.VuetifyTemplate``.
        """

        # initialize the table cache, so the ``table_options`` observer is safe to fire
        # if that traitlet is passed in via ``kwargs``.
        self._all_items = None
        self._aladin_fileset_overlay = None
        self._aladin_fileset_app = None

        super().__init__(**kwargs)

        self.table = table
        self.table[col_unique_row_index] = np.arange(len(table))
        self.app = app

        # serialization
        if not self.table_options:
            self.table_options = {'page': 1, 'itemsPerPage': self.items_per_page}

        self._all_items = self.table
        self.server_items_length = len(self._all_items)
        self._push_current_page()

        columns = self.table.colnames

        if not self.item_key:
            self._set_item_key(columns, unique_column)

        # headers_avail excludes the unique row index column, and headers_visible
        # defaults to exclude the `s_region` column (can be undone in the UI)
        self.headers_avail = [
            column for column in columns if column != col_unique_row_index
        ]
        self.headers_visible = [
            column for column in self.headers_avail if column != 's_region'
        ]

        self.column_descriptions = []

        if detected_mission := validate.detect_mission_or_products(table):
            if not self.mission:
                self.mission = detected_mission

            self.column_descriptions = validate.get_column_descriptions(
                detected_mission, table
            )

            # if the user hasn't defined the ra/dec columns, use
            # the expected MastMissions names for this mission:
            if ra_column is None and dec_column is None:
                ra_column, dec_column = mission_mast_ra_dec_colnames[detected_mission]

        self._update_enable_load_in_app()

        # create headers with expected vuetify3 formatting and descriptions
        self.headers = [
            {
                "title": name,
                "key": name,
                "description": self._get_header_description(name)
            }
            for name in table.colnames
        ]

        # conditional updating of MastAladin app target based on ra/dec
        if (
            ra_column in columns and
            dec_column in columns and
            update_viewport and
                self.app is not None):

            # use the first sky coordinate as a reference for centering the viewer.
            # an alternative would be to use e.g. mean(RA), though means would return an
            # unhelpful coordinate in the case where observations span the meridian or poles.
            reference_coord = SkyCoord(
                ra=self.table[ra_column][0] * u.deg,
                dec=self.table[dec_column][0] * u.deg,
                unit=u.deg
            )

            # set the center of the viewer on the reference coord:
            self.app.target = f"{reference_coord.ra.degree} {reference_coord.dec.degree}"

    @observe('table_options')
    def _table_options_changed(self, msg):
        if not self.server_pagination or self._all_items is None:
            return
        self._push_current_page()

    def update_items(self, table):
        """Update the table data and refresh the current page."""
        self._all_items = table
        self.server_items_length = len(self._all_items)
        self._push_current_page()

    def _push_current_page(self):
        """Push only the current page of the table to ``items``."""
        if self._all_items is None:
            self.items = []
            return
        table = self._all_items
        if not self.server_pagination:
            self.items = serialize(table)
            return
        opts = self.table_options or {}
        page = opts.get('page', 1)
        per_page = opts.get('itemsPerPage', self.items_per_page)

        # Apply sorting before pagination.
        if self.sort_by:
            sort = self.sort_by[0]
            key = sort["key"]
            reverse = sort["order"] == "desc"
            order = np.argsort(table[key], kind="stable")
            if reverse:
                order = order[::-1]
            table = table[order]

        # "All" option: serialize the full table intentionally.
        if per_page == -1:
            self.items = serialize(table)
            return
        start = (page - 1) * per_page
        end = start + per_page
        page_table = table[start:end]
        self.items = serialize(page_table)

    def _set_item_key(self, table_columns, item_key, n_rows_slow=10e6):
        """
        `item_key` should be set to the name of a table column that contains
        unique values in each row, which can be used for selection.

        If no `unique_column` is given at construction, look for a column known to have
        unique values for each row in MAST catalog and observation queries. If no known
        columns are found, search through the table to find a column with unique rows.

        Unique row searches are inefficient for tables with more than `n_rows_slow` rows,
        and a warning will be raised. The default `n_rows_slow = 10e6` takes about 100
        milliseconds per table column.
        """
        if item_key is None:
            # check for known unique columns:
            for column in known_unique_mast_table_cols:
                if column in table_columns:
                    self.item_key = column
                    break

            # warn the user if unique row search will be inefficient:
            if len(self.table) > n_rows_slow:
                warnings.warn(
                    "No `unique_column` was given, so all columns will be checked "
                    f"for unique entries. This table has {len(self.table)} rows, so "
                    "the search for unique rows may be slow. To avoid this in the future,"
                    "use the `unique_column` keyword argument when calling "
                    "`MastAladin.load_table`.", UserWarning
                )

            # search for columns with unique rows:
            for column in table_columns:
                n_unique_values = np.unique(self.table[column]).size
                if n_unique_values == len(self.table):
                    self.item_key = column
                    break
            else:
                raise ValueError(
                    "No `unique_column` specified, and no unique columns were found."
                )

        elif item_key in table_columns:
            self.item_key = item_key

        else:
            raise ValueError(
                f"item_key '{item_key}' not found in table columns: {table_columns}"
            )

    def _get_header_description(self, name):
        for entry in self.column_descriptions:
            if entry["name"] == name:
                return entry["description"]
        return None

    @observe('selected_rows')
    def _on_row_selection(self, msg={}):
        for func in self.row_select_callbacks:
            func(msg)

    @property
    def selected_rows_table(self):
        """
        `~astropy.table.Table` of only the selected rows.
        """
        return self.table[[int(value) for value in self.selected_rows]]

    def vue_open_selected_rows_in_jdaviz(self, *args):
        viz = jd.gca()
        selected_rows_table = self._selected_rows_table_from_args(args)

        if self._can_open_footprints:
            regions = self._s_regions_from_table(selected_rows_table)

            if not regions:
                return viz

            footprints = viz.plugins['Footprints']
            orientation = viz.plugins['Orientation']
            current_alignment = getattr(
                orientation.align_by, 'selected', orientation.align_by
            )
            if current_alignment != 'WCS':
                orientation.align_by = 'WCS'

            # footprint marks are only rendered while the plugin is active
            footprints.open_in_tray(scroll_to=False)
            footprints.keep_active = True

            overlay = 'mast-table selection'
            for existing_overlay in list(footprints.overlay.choices):
                if (
                    existing_overlay == overlay
                    or existing_overlay.startswith(f'{overlay} ')
                ):
                    footprints.remove_overlay(existing_overlay)

            # drop the previous import so the new overlay isn't given cached regions
            if footprints.preset.selected == 'From File...':
                footprints.preset.selected = footprints.preset.choices[0]

            footprints.add_overlay(overlay)
            footprints.import_region(Regions([
                stcs_string2region(region)
                for region in regions
            ]))
            if 'default' in footprints.overlay.choices:
                footprints.remove_overlay('default')
            return viz

        with viz.batch_load():
            for filename in selected_rows_table['filename']:
                _download_from_mast(filename)
                viz.load(filename, format="Image")

        orientation = viz.plugins['Orientation']
        orientation.align_by = 'WCS'
        orientation.set_north_up_east_left()

        plot_options = viz.plugins['Plot Options']
        if len(plot_options.layer.choices) > 1:
            for layer in plot_options.layer.choices:
                plot_options.layer = layer
                plot_options.image_color_mode = 'Color'

            plot_options.apply_RGB_presets()

        return viz

    def vue_open_selected_rows_in_aladin(self, *args):
        from mast_aladin.app import gca

        mal = gca()
        selected_rows_table = self._selected_rows_table_from_args(args)

        if self._can_open_footprints:
            regions = self._s_regions_from_table(selected_rows_table)

            if not regions:
                return mal

            if (
                self._aladin_fileset_overlay is not None
                and self._aladin_fileset_app is mal
            ):
                mal.remove_overlay(self._aladin_fileset_overlay)
                self._aladin_fileset_overlay = None

            self._aladin_fileset_overlay = mal.add_graphic_overlay_from_stcs(
                regions,
                name='mast-table selection',
            )
            self._aladin_fileset_app = mal

            return mal

        for filename in selected_rows_table['filename']:
            _download_from_mast(filename)
            mal.delayed_add_fits(filename)

        return mal

    def _selected_s_regions(self):
        return self._s_regions_from_table(self.selected_rows_table)

    def _selected_rows_table_from_args(self, args):
        selected_rows = (
            args[0]
            if args and isinstance(args[0], list)
            else self.selected_rows
        )
        return self.table[[int(value) for value in selected_rows]]

    def _s_regions_from_table(self, table):
        regions = []
        for region in table['s_region']:
            if np.ma.is_masked(region) or not str(region).strip():
                continue
            regions.extend(
                value.strip()
                for value in re.split(
                    r'(?=\b(?:POLYGON|CIRCLE|ELLIPSE)\b)',
                    str(region),
                    flags=re.IGNORECASE,
                )
                if value.strip()
            )
        return regions

    @property
    def _is_product_list(self):
        return (self.mission or '').lower() == 'list_products'

    @property
    def _can_open_footprints(self):
        return (
            (self.mission or '').lower() in validate.missions
            and 's_region' in self.table.colnames
        )

    def _update_enable_load_in_app(self):
        self.enable_load_in_app = (
            self._is_product_list or self._can_open_footprints
        )

    @observe('mission')
    def _on_mission_update(self, msg={}):
        self._update_enable_load_in_app()


def _download_from_mast(product_file_name):
    if os.path.exists(product_file_name):
        # support load from cache without query to MM
        return

    # temporarily support JWST and HST until Roman is also available:
    if product_file_name.startswith('jw'):
        mission = 'jwst'
    elif product_file_name.startswith('r'):
        mission = 'roman'
    else:
        mission = 'hst'

    MastMissions(mission=mission).download_file(product_file_name)
