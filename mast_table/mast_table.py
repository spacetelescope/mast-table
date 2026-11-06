import warnings


from IPython.display import display
from sidecar import Sidecar
import ipywidgets as widgets

from mast_table.base import BaseMastTable, col_unique_row_index
from mast_table.components import MastTableView


from typing import List, Optional, Callable

import solara


# register loaded table widgets as they're initialized
_table_widgets = []

__all__ = [
    'get_current_table',
    'MastTable',
    'SelectableTable',
]


class MastTable:
    """
    A selectable table with row filtering.
    """

    def __init__(self, table, **kwargs):
        """
        Parameters
        ----------
        table : `~astropy.table.Table`
            A table to load.

        **kwargs
            Keyword arguments are passed to `~mast_table.base.BaseMastTable` and
            `~mast_table.components.MastTableView`.
        """
        _table_widgets.append(self)

        self._mast_table_source = table
        self.widget = BaseMastTable(
            table,
            item_key=col_unique_row_index,
            **kwargs,
        )
        self.sidecar = kwargs.get("sidecar", None)
        self.popout_button = None

    def __getattr__(self, name):
        return getattr(self.widget, name)

    @property
    def selected_rows(self):
        return self.widget.selected_rows

    @selected_rows.setter
    def selected_rows(self, value):
        if value and isinstance(value[0], dict):
            value = [item[col_unique_row_index] for item in value]
        self.widget.selected_rows = value

    @property
    def selected_rows_table(self):
        return self.table[[int(value) for value in self.widget.selected_rows]]

    @property
    def items(self):
        return self.widget.items

    @items.setter
    def items(self, value):
        self.widget.items = value

    def _set_popout_button(self, popout_button):
        self.popout_button = popout_button

    def _ipython_display_(self):
        display(
            MastTableView(
                self._mast_table_source,
                base_mast_table=self.widget,
                on_popout_button=self._set_popout_button,
            )
        )

    def show(self, loc="inline", title="mast-table", ref=None):
        """
        Display MastTable.

        Parameters
        ----------
        loc : str, optional. Default "inline"
            Location to display the MastTable. Supported locations include:

            - "inline": Displays the MastTable inline in a notebook.
            - "sidecar": Displays the MastTable in a separate JupyterLab window from the
              notebook, with location decided by 'anchor'. Anchor options available from
              ``jupyterlab-sidecar`` are: {'split-right', 'split-left', 'split-top',
              'split-bottom', 'tab-before', 'tab-after', 'right'}.
              Example ``loc`` for a sidecar at the bottom is ``loc='sidecar:split-bottom'``.

            - "popout": Display the MastTable in a detached display. By default, a new
              window will open (browser popup permissions required). Anchor options are
              ``popout:window`` (default, opens MastTable in a new, detached popout) or
              ``popout:tab`` (opens MastTable in a new, detached tab in your browser).

        title : str, optional. Default "mast-table"
            The title of the sidecar tab, only applicable to a "sidecar" display.

        ref : sidecar.Sidecar [1]_ or app, optional. Default None.
            An existing reference sidecar or app with ``.sidecar`` attribute. Opens the new sidecar
            display with its anchor defined relative to the ref sidecar. Only applicable to a
            "sidecar" display.

        References
        ----------
        .. [1] `JupyterLab Sidecar
               <https://github.com/jupyter-widgets/jupyterlab-sidecar#sidecar>`_
        """
        valid_anchors = [
            "split-right", "split-left", "split-top", "split-bottom",
            "tab-before", "tab-after", "right", None
        ]

        if type(loc) is not str:
            raise TypeError("Invalid loc type provided. Must be a string.")

        if loc == "inline":
            self._ipython_display_()
        elif loc.startswith("sidecar"):
            anchor = None if loc == "sidecar" else loc.split(":")[-1]

            if anchor not in valid_anchors:
                raise ValueError(
                    "Invalid anchor provided. Must be one of the available from "
                    "``jupyterlab-sidecar``. Valid anchors are: "
                    f"{valid_anchors[:-1]}")

            if ref and not isinstance(ref, Sidecar):
                try:
                    ref = ref.sidecar
                except AttributeError:
                    raise ValueError(
                        "Invalid ref provided. Must be a `Sidecar` instance or an "
                        "app with `.sidecar` attribute."
                    )

                if ref is None or not isinstance(ref, Sidecar):
                    raise ValueError(
                        "Invalid ref provided. App must have an initialized `.sidecar` "
                        "attribute."
                    )

            sc = Sidecar(title=title, anchor=anchor, ref=ref)
            with sc:
                self._ipython_display_()
            self.sidecar = sc

        elif loc.startswith("popout"):
            if self.popout_button is None:
                self._hidden_output = widgets.Output()
                self._hidden_output.layout.display = "none"

                with self._hidden_output:
                    self._ipython_display_()

            anchor = None if loc == "popout" else loc.split(":")[-1]
            if anchor in (None, "window"):
                self.popout_button.open_window()
            elif anchor == "tab":
                self.popout_button.open_tab()
            else:
                raise ValueError(
                    "Invalid anchor provided. Must be 'window' or 'tab'."
                )
        else:
            raise ValueError("Invalid loc provided. Must be 'inline', 'sidecar', or 'popout'.")


def get_current_table():
    """
    Return the last instantiated table widget, warns user
    if none exist.
    """
    if _table_widgets:
        return _table_widgets[-1]
    else:
        warnings.warn(
            "No `MastTable` exists.", UserWarning
        )


@solara.component
def SelectableTable(
    table,
    base_mast_table,
    on_selected_indices: Optional[Callable[[List[int]], None]] = None,
    drawer_open: bool = False,
    set_drawer_open=None
):
    """An ipyvuetify DataTable with checkbox selection.

    Displays a paginated table with selectable rows.  Reports the
    indices (into *table*) of the currently selected rows.

    Parameters
    ----------
    table : `~astropy.table.Table`
        A table to load.

    base_mast_table : `~mast_table.base.BaseMastTable`
        BaseMastTable widget to display.

    on_selected_indices : callable (optional, default is `None)
        Callback on selected indices.

    drawer_open : bool (optional, default is `True`)
        If `True`, the CrossFilterMenu sidepanel is initialized
        open.

    set_drawer_open: callable (optional, default is `None)
        Callback to open CrossFilterMenu sidepanel.

    """
    selected, set_selected = solara.use_state([])

    # Build vuetify column headers from the table
    def handle_input(msg):
        new_entries = msg["new"]
        set_selected(new_entries)

        if on_selected_indices is not None and len(new_entries):
            indices = [int(index) for index in new_entries]
            on_selected_indices(indices)

    def on_change(change):
        set_drawer_open(change["new"])

    base_mast_table.filter_tray_open = drawer_open

    base_mast_table.selected_rows = [
        item[col_unique_row_index]
        for item in base_mast_table.items
        if item[col_unique_row_index] in selected
    ]

    def observe_widget(base_mast_table, on_change, handle_input):
        base_mast_table.observe(on_change, "filter_tray_open")
        base_mast_table.observe(handle_input, "selected_rows")

    solara.use_effect(
        lambda: observe_widget(
            base_mast_table,
            on_change,
            handle_input,
        ),
        [base_mast_table],
    )

    # updating BaseMastTable items on filter changes
    solara.use_effect(
        lambda: base_mast_table.update_items(table),
        [table],
    )

    display(base_mast_table)
