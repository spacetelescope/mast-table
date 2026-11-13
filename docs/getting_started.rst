.. _getting_started:

.. |jwst_search| raw:: html

   <a href="https://mast.stsci.edu/search/ui/#/jwst" target="_blank">JWST Search</a>

.. |jwst_search_result| raw:: html

   <a href="https://mast.stsci.edu/search/ui/#/jwst/results?resolve=true&target=9.701+40.76&radius=8"
   target="_blank">Follow this link to see results for the above query</a>


Getting started
===============

In this example, we'll query MAST for JWST observations of a stellar merger
event and explore the data using ``mast-table``.

Query MAST
----------

Let's use `astroquery <https://astroquery.readthedocs.io/en/latest/>`_ to
search for JWST observations with `~astroquery.mast.missions.MastMissionsClass`:

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


.. admonition:: Non-python alternative: JWST Search via webform
   :class: tip

   To query MAST in your web browser, use |jwst_search|.
   JWST Search will display query results as a table, and plot 
   the observation footprints on the Aladin full-sky atlas. 
   |jwst_search_result|.

   .. image:: https://github.com/spacetelescope/widget-docs/blob/main/mast-table/getting_started/jwst-query-result.jpg?raw=true
       :target: https://mast.stsci.edu/search/ui/#/jwst/results?resolve=true&target=9.701+40.76&radius=8
       :width: 100%
       :align: center
       :class: outlined
    

Astroquery returns a `astropy.table.Table` object with the MAST query results.
We can interact with the results using ``mast-table``.

Launch mast-table
-----------------

Initialize the `~mast_table.mast_table.MastTable` widget with:

.. code-block:: python

    from mast_table import MastTable

    mast_table = MastTable(observations)

    mast_table.show()


.. image:: https://github.com/spacetelescope/widget-docs/blob/main/mast-table/getting_started/cell0.png?raw=true
    :width: 100%
    :align: center
    :class: no-click

|

By default, `~mast_table.mast_table.MastTable.show` will display the 
widget in the cell output below the code cell.

Pagination
~~~~~~~~~~

The table footer tells us that the results are paginated with 10 items per page,
and 67 observations total (see table footer). Click the arrows on the right
of the table footer to advance through the pages.

Browse results
--------------

Hover over column names to see their descriptions. Click the arrow
next to a column name to sort the table by that column's values in
ascending or descending order:

.. image:: https://github.com/spacetelescope/widget-docs/blob/main/mast-table/getting_started/cell0-desc.png?raw=true
    :width: 100%
    :align: center
    :class: no-click



Selection
---------

Click the checkboxes on the left of a row to select an observation:

.. image:: https://github.com/spacetelescope/widget-docs/blob/main/mast-table/getting_started/cell0-selected.png?raw=true
    :width: 100%
    :align: center
    :class: no-click

|


Filters
-------

Use the "Filters" button in the top left to filter down the visible
observations to those that meet some criteria. Let's make visible *only* the
observations with the exposure type (``exp_type``) column value corresponding
to MIRI imaging (``MIR_IMAGE``):

.. image:: https://github.com/spacetelescope/widget-docs/blob/main/mast-table/getting_started/cell0-filter.png?raw=true
    :width: 100%
    :align: center
    :class: no-click

|

Multiple filters
~~~~~~~~~~~~~~~~

Multiple filters can be used together to narrow down the observations further:

.. image:: https://github.com/spacetelescope/widget-docs/blob/main/mast-table/getting_started/cell0-filter-multi.png?raw=true
    :width: 100%
    :align: center
    :class: no-click

| 

Filter logic
~~~~~~~~~~~~

Combine filters with the logical operators "AND" or "OR" using the buttons
at the top, or click the circular arrow to clear all filters:

.. image:: https://github.com/spacetelescope/widget-docs/blob/main/mast-table/getting_started/cell0-filter-operators.png?raw=true
    :width: 100%
    :align: center
    :class: no-click

| 


