.. |jwst_search| raw:: html

   <a href="https://mast.stsci.edu/search/ui/#/jwst" target="_blank">JWST Search</a>


.. |jwst_search_result| raw:: html

   <a href="https://mast.stsci.edu/search/ui/#/jwst/results?resolve=true&target=9.701+40.76&radius=8"
   target="_blank">Click here to see this JWST Search result on the MAST website.</a>

.. |rrn| raw:: html

  <a href="https://roman.science.stsci.edu" target="_blank">Roman Research Nexus</a>


.. |sidecar| raw:: html

  <a href="https://github.com/jupyter-widgets/jupyterlab-sidecar" target="_blank">sidecar.Sidecar</a>


.. |motorcycle| raw:: html

  <a href="https://github.com/spacetelescope/motorcycle" target="_blank">motorcycle</a>


With mast-aladin
================

Let's visualize observation footprints on the sky using ``mast-table`` and 
`mast-aladin <https://mast-aladin.readthedocs.io/en/latest/>`_, a Jupyter widget for visualizing 
footprints, catalogs, and imaging data products on survey images.

As we showed in :doc:`getting_started`, |jwst_search| results on the web are shown in a table and
an Aladin widget:

.. image:: https://github.com/spacetelescope/widget-docs/blob/main/mast-table/getting_started/jwst-query-result.jpg?raw=true
    :target: https://mast.stsci.edu/search/ui/#/jwst/results?resolve=true&target=9.701+40.76&radius=8
    :width: 100%
    :align: center
    :class: outlined

|

|jwst_search_result|

``mast-table`` and ``mast-aladin`` have been designed to produce a similar interactive environment 
**in Jupyter Lab**.

Observation query
-----------------

As we did in :doc:`getting_started`, let's use astroquery to retrieve an observation query result table.

.. code-block:: python

    from astroquery.mast import MastMissions

    import astropy.units as u
    from astropy.coordinates import SkyCoord    

    coord = SkyCoord(ra=9.701, dec=40.76, unit=u.deg)

    mission_search = MastMissions(mission='jwst')
    observations = mission_search.query_region(
        coordinates=coord,    # location of stellar merger
        radius=8 * u.arcmin   # cone search radius
    )

Observation query results from `~astroquery.mast.missions.MastMissionsClass`
are returned as an `astropy.table.Table`.  Notice that the ``observations``
table has a column called ``s_regions``. The values are 
`STC-S region <https://ivoa.net/documents/STC-S/>`_ strings which describe the
observation footprint.

.. code-block:: python

    >>> print(observations['s_region'][0])

    POLYGON ICRS  9.687987533 40.746149162 9.728729822 40.751207282 9.722084892 40.782215316 9.681196186 40.777432264

Let's initialize a `~mast_table.mast_table.MastTable` widget with the query results.

.. code-block:: python

    from mast_table import MastTable

    mast_table = MastTable(observations)


Launch mast-aladin
------------------

Let's initialize a `~mast_aladin.app.MastAladin` widget. We will center on
the query coordinate by setting ``target``, and we'll set  the field of view or
"zoom level" with ``fov``.

We load the observation table into ``mast-aladin`` with 
`~mast_aladin.app.MastAladin.add_table`.

.. code-block:: python

    from mast_aladin import MastAladin

    mast_aladin = MastAladin(
        target=coord,  # center sky coordinate
        fov=0.25       # field of view [degrees]
    )

    # load observation query results into mast-aladin
    overlay = mast_aladin.add_table(observations)

Now we call the ``show`` methods on `~mast_aladin.app.MastAladin` and 
`~mast_table.mast_table.MastTable` to display these results in a 
Jupyter Lab environment, like the |rrn|.

.. code-block:: python

    # show both widgets in Jupyter Lab
    mast_table.show()
    mast_aladin.show()

The Jupyter Lab workspace now looks like this:

.. image:: https://github.com/spacetelescope/widget-docs/blob/main/mast-table/mast-table-and-aladin.jpg?raw=true
    :width: 100%
    :align: center
    :class: outlined

|

The widget visualizes the sky with imaging from STScI's 
`Digitized Sky Survey <https://archive.stsci.edu/dss/>`_ (by default) and others.

Widget arrangement
------------------

By default, ``mast-table`` is shown in the output beneath the code cell, and ``mast-aladin`` is
opened in a |sidecar| to the right of the notebook. You can click and drag the ``mast-aladin``
tab label to rearrange your workspace.

We can also configure the placement of the widgets by adding arguments to 
`~mast_table.mast_table.MastTable.show`. In this example, we open both widgets
in their own sidecars beneath the notebook, with ``mast-table`` on the left
and ``mast-aladin`` on the right:


.. code-block:: python

    # alternative widget arrangement
    mast_table.show('sidecar:split-bottom')

    # place mast-aladin to the right of reference widget `mast_table`
    mast_aladin.show('sidecar:split-right', ref=mast_table)


.. image:: https://github.com/spacetelescope/widget-docs/blob/main/mast-table/table-aladin-sidecars.jpg?raw=true
    :width: 100%
    :align: center
    :class: outlined

motorcycle: extra arrangement help
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have several tabs open, sometimes it might takes a few clicks and drags to reorganize your Jupyter
Lab workspace. To save you clicks, we developed |motorcycle| -- a Jupyter Lab extension
that drives around your sidecars. ``motorcycle`` comes pre-installed on the |rrn|, and you can
install it locally with::

    pip install motorcycle

``motorcycle`` adds a "Layout" dropdown to the Jupyter Lab menu bar, which exposes several 
options for reorganizing your notebooks and sidecars with fewer clicks.

.. image:: https://github.com/spacetelescope/widget-docs/blob/main/mast-table/motorcycle.gif?raw=true
    :width: 100%
    :align: center
    :class: outlined