import os
import pytest
import numpy as np
from astropy.nddata import NDData
from astropy.table import Table
from astropy.wcs import WCS


@pytest.fixture
def mast_observation_table():
    """
    To reproduce the table file, run:

        from astroquery.mast.missions import MastMissions

        mast = MastMissions(mission='jwst')
        result = mast.query_object("M4", limit=5)
        result.write("mm_jwst_M4.ecsv")
    """
    path = os.path.join(
        os.path.dirname(__file__), "tests", "data", "mm_jwst_M4.ecsv"
    )
    return Table.read(path)


@pytest.fixture
def jdaviz_app():
    """
    A jdaviz app set as the current app, with an image loaded so the
    Footprints plugin has a reference WCS to map footprints onto.
    """
    jdaviz = pytest.importorskip('jdaviz')

    app = jdaviz.new_app(set_as_current=True)

    wcs = WCS({
        'CTYPE1': 'RA---TAN', 'CUNIT1': 'deg', 'CDELT1': -0.001,
        'CRPIX1': 25, 'CRVAL1': 245.9,
        'CTYPE2': 'DEC--TAN', 'CUNIT2': 'deg', 'CDELT2': 0.001,
        'CRPIX2': 25, 'CRVAL2': -26.5,
    })
    app.load(NDData(np.zeros((50, 50)), wcs=wcs))

    return app
