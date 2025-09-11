from mast_aladin.table import MastTable


def test_mast_table_init(mast_observation_table):
    mast_table = MastTable(mast_observation_table)

    # check that astropy table is stored on the widget
    assert 's_region' in mast_table.table.colnames

    # check that s_region col exists in available widget columns
    assert 's_region' in mast_table.headers_avail

    # check that s_region col isn't visible by default
    assert 's_region' not in mast_table.headers_visible

    # the MAST observation query has a ArchiveFileID column,
    # which should be chosen as the default item_key:
    assert mast_table.item_key == 'ArchiveFileID'
