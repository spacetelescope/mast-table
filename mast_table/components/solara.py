import functools
import operator
import uuid
from typing import List, Callable

from ipypopout import PopoutButton
import reacton.ipyvuetify as v
import solara

from astropy.table import Table
from mast_table.utils import (
    operator_map, table_filter_values, table_range,
    slide_or_select, step_size, build_select_items,
    build_select_filter_preview,
)

from mast_table.base import col_unique_row_index
from mast_table.components.cross_filter_select import Select
from mast_table.components.cross_filter_input import Input
from mast_table.components.alert import Alert


__all__ = [
    'CrossFilterSelect',
    'CrossFilterSlider',
    'FilterModeButtons',
    'SettingsMenu',
    'RemoveFilterButton',
    'MastTableView',
]


def preserve_docstring(func):
    # when a function is decorated with `solara.component`,
    # the function's docstring is not passed through to the
    # wrapped function unless you also use this decorator.

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@preserve_docstring
@solara.component
def FilterModeButtons(
    mode,
    set_mode,
    dense=False
):
    """
    Comparison operator selector for slider widgets.

    Parameters
    ----------
    mode : str
        The mode to use for filtering. Can be one of `==`, `>=`, `<=`, `>`, `<`.
    set_mode : callable
        Callback for updating filter's mask.
    dense : bool
        Boolean to condense button options.

    """
    with solara.ToggleButtonsSingle(
        value=mode,
        on_value=set_mode,
        dense=dense
    ):
        solara.Button(
            icon_name="mdi-code-equal",
            icon=True,
            value="==",
        )
        solara.Button(
            icon_name="mdi-code-not-equal",
            icon=True,
            value="!=",
        )
        solara.Button(
            icon_name="mdi-code-less-than",
            icon=True,
            value="<",
        )
        solara.Button(
            icon_name="mdi-code-less-than-or-equal",
            icon=True,
            value="<=",
        )
        solara.Button(
            icon_name="mdi-code-greater-than",
            icon=True,
            value=">",
        )
        solara.Button(
            icon_name="mdi-code-greater-than-or-equal",
            icon=True,
            value=">=",
        )


@preserve_docstring
@solara.component
def SettingsMenu(
    invert,
    set_invert,
    multiple=None,
    set_multiple=None
):
    """
    A menu for widgets that manages options for mode, inversion, and multiple.

    Parameters
    ----------
    invert : bool
        Whether to invert the selection.
    set_invert : callable
        Callback for updating filter's inversion.
    multiple : bool
        Whether to allow multiple values to be selected.
    set_multiple : callable
        Callback for updating filter's ability to select multiple values.

    """
    with v.Container(
        fluid=True,
        class_="pa-0 ma-0",
    ):
        v.Switch(
            v_model=invert,
            on_v_model=set_invert,
            label="Invert filter",
            hide_details=True,
            density="compact",
            color="primary"
        )

        if multiple is not None:
            v.Switch(
                v_model=multiple,
                on_v_model=set_multiple,
                label="Select multiple",
                hide_details=True,
                density="compact",
                color="primary"
            )


@preserve_docstring
@solara.component
def RemoveFilterButton(
    filter_id: str,
    on_remove=None,
):
    """
    Button for removal of filter.

    Parameters
    ----------
    filter_id : str
        The unique filter instance ID.
    on_remove : callable, optional
        Callback to remove this filter from parent filter list.

    """
    solara.Button(
        icon_name="mdi-close",
        on_click=lambda: on_remove(filter_id),
        style={"background-color": "light-dark(#00617e, #013b4d)", "color": "white"},
        classes=["close-button"],
    )
    solara.Style(
        """
        .close-button {
            min-width: 40px;
            width: 40px;
            height: 30px;
            padding: 0;
        }
        """
    )


@preserve_docstring
@solara.component
def CrossFilterSelect(
    table: Table,
    column: str,
    filter_id: str,
    set_mask: Callable,
    set_filter_mode: Callable,
    table_filtered: Table,
    initial_values=None,
    max_unique: int = 100,
    multiple: bool = False,
    invert: bool = False,
    configurable: bool = True,
    classes: List[str] = [],
):
    """
    A Select widget that will cross filter an astropy Table.

    Parameters
    ----------
    table : `astropy.table.Table`
        The astropy Table to filter.
    column : str
        The column to filter on.
    filter_id : str
        The unique filter instance ID.
    set_mask : callable
        Callback for updating filter's mask.
    set_filter_mode : callable
        Callback for updating filter mode
    table_filtered : `astropy.table.Table`
        Table after filtering.
    initial_values : list, optional
        The initial values to set as selected. Default is None.
    max_unique : int, optional
        The maximum number of unique values to show in the dropdown. Default is 100.
    multiple : bool
        Whether to allow multiple values to be selected. Default is False.
    invert : bool
        Whether to invert the selection. Default is False.
    configurable : bool
        Whether to show the configuration button. Default is True.
    classes : list
        Additional CSS classes to add to the main widget.

    """
    if initial_values is None:
        initial_values = []
    elif isinstance(initial_values, str):
        initial_values = [initial_values]

    filter_values, set_filter_values = solara.use_state(initial_values)
    solara.use_effect(
        lambda: set_filter_values(initial_values or []),
        [initial_values],
    )
    invert, set_invert = solara.use_state_or_update(invert)
    multiple, set_multiple = solara.use_state_or_update(multiple)

    def update_mode(new_invert):
        set_invert(new_invert)
        set_filter_mode("!=" if new_invert else "==")

    def clear_not_multiple():
        if not multiple and len(filter_values) > 1:
            set_filter_values([filter_values[0]])

    solara.use_effect(
        clear_not_multiple,
        [multiple]
    )

    items, value_counts = build_select_filter_preview(
        table,
        column,
        max_unique=max_unique,
        table_filtered=table_filtered
    )

    def set_values_and_filter(values):
        if values is None:
            set_filter_values([])
            return

        if multiple:
            set_filter_values([value["value"] for value in values])
        else:
            set_filter_values([values["value"]])

    def reset():
        set_filter_values([])

    solara.use_memo(reset, dependencies=[column])

    def update_filter():
        if hasattr(table[column], 'mask'):
            unmasked_values_as_strings = (
                list(table[column].data[~table[column].mask].astype(str)) +
                ['--']  # masked value
            )
        else:
            unmasked_values_as_strings = table[column].astype(str)
        if (
            len(filter_values) == 0 or
            (not invert and set(filter_values).issuperset(unmasked_values_as_strings))
        ):
            set_mask(filter_id, None)
            return

        mask = table_filter_values(table, column, filter_values, invert=invert)
        set_mask(filter_id, mask)

    solara.use_memo(update_filter, dependencies=[filter_values, invert])

    if multiple:
        value = [item for item in items if item["value"] in filter_values]
    else:
        if filter_values:
            value = next(
                (item for item in items if item["value"] == filter_values[0]),
                None,
            )
        else:
            value = None

    with solara.VBox(classes=classes) as main:
        with solara.Column():
            if len(items) < 5:
                # set styling for compact checkboxes
                solara.Style(
                    """
                    .compact-checkboxes .v-selection-control {
                        min-height: 24px;
                        padding: 0;
                    }

                    .compact-checkboxes .v-selection-control__wrapper {
                        height: 24px;
                    }

                    .compact-checkboxes .v-label {
                        margin: 0;
                    }
                    """
                )

                with v.Container(
                    fluid=True,
                    class_="pa-0 ma-0 compact-checkboxes",
                ):
                    for opt in items:
                        checked = opt["value"] in filter_values

                        def toggle_value(checked, value=opt["value"]):
                            if checked:
                                set_filter_values(filter_values + [value])
                            else:
                                set_filter_values(
                                    [v for v in filter_values if v != value]
                                )

                        v.Checkbox(
                            v_model=checked,
                            on_v_model=toggle_value,
                            label=opt["text"],
                            density="compact",
                            hide_details=True,
                        )

                    with solara.Row(
                        style={
                            "align-items": "center",
                            "justify-content": "space-between",
                            "width": "100%",
                            "padding": 0,
                        }
                    ):
                        solara.Button(
                            "Select All",
                            on_click=lambda: set_filter_values(
                                [item["value"] for item in items]
                            ),
                            text=True,
                            style={
                                "background-color": "light-dark(#00617e, #013b4d)",
                                "color": "white"
                            }
                        )

                        solara.Button(
                            "Clear All",
                            on_click=lambda: set_filter_values([]),
                            text=True,
                            style={
                                "background-color": "light-dark(#00617e, #013b4d)",
                                "color": "white"
                            }
                        )

            else:
                # creating selection dropdown
                Select.element(
                    value=value,
                    items=items,
                    on_value=set_values_and_filter,
                    label="",
                    clearable=False,
                    return_object=True,
                    multiple=multiple,
                    filtered=len(filter_values) > 0,
                    count=len(table_filtered),
                    messages=(
                        f"Too many unique values, will only show the first {max_unique}"
                        if len(value_counts) > max_unique else ""
                    ),
                )

                # creating settings menu
                if configurable:
                    SettingsMenu(
                        invert,
                        update_mode,
                        multiple=multiple,
                        set_multiple=set_multiple
                    )

    return main


@preserve_docstring
@solara.component
def CrossFilterSlider(
    table,
    column: str,
    filter_id: str,
    set_mask: Callable,
    set_filter_mode: Callable,
    initial_value=None,
    mode: str = ">=",
    configurable: bool = True,
):
    """
    A Slider widget that will cross filter an astropy Table.

    See ``use_cross_filter`` for more information about how to use cross filtering.

    Parameters
    ----------
    table : `astropy.table.Table`
        The astropy Table to filter.
    column : str
        The column to filter on.
    filter_id : str
        The unique filter instance ID.
    set_mask : callable
        Callback for updating filter's mask.
    set_filter_mode : callable
        Callback for updating filter's mode.
    initial_value : float, optional
        The initial value to set for the slider.
    mode : str, optional
        The mode to use for filtering. Can be one of `==`, `>=`, `<=`, `>`, `<`.
    configurable : bool
        Whether to show a configuration button. Default is True.

    """
    filter_value, set_filter_value = solara.use_state(initial_value)
    solara.use_effect(
        lambda: set_filter_value(initial_value),
        [initial_value],
    )
    mode, set_mode = solara.use_state_or_update(mode)

    def update_mode(new_mode):
        set_mode(new_mode)
        set_filter_mode(new_mode)

    vmin, vmax = table_range(table, column)

    def reset():
        if initial_value is not None:
            set_filter_value(initial_value)
        else:
            set_filter_value(vmin)

    solara.use_memo(reset, dependencies=[column])

    def update_filter():
        filter = None
        if filter_value:
            filter = operator_map[mode](table[column], filter_value)
        set_mask(filter_id, filter)

    solara.use_memo(update_filter, dependencies=[filter_value, mode])

    with solara.VBox() as main:
        solara.Style(
            """
            .crossfilter-slider .v-slider {
                transform: translateY(10px);
            }
            """
        )

        slider_args = {
            "label": "",
            "min": vmin,
            "max": vmax,
            "step": step_size(vmin, vmax),
            "thumb_label": False,
            "tick_labels": False,
            "color": "primary",
        }

        # creating slider
        with solara.Row(
            style={"alignItems": "center"},
            classes=["crossfilter-slider"]
        ):
            Input.element(
                value=filter_value,
                min=vmin,
                max=vmax,
                step=step_size(vmin, vmax),
                on_value=set_filter_value,
            )

            v.Slider(
                v_model=filter_value,
                on_v_model=set_filter_value,
                **slider_args
            )

        # creating settings menu
        if configurable:
            FilterModeButtons(
                mode=mode,
                set_mode=update_mode,
                dense=True,
            )

    return main


@preserve_docstring
@solara.component
def MastTableView(table, base_mast_table, on_popout_button=None):
    """
    Displays selectable table with cross-filtering.

    Parameters
    ----------
    table : `~astropy.table.Table`
        A table to load.

    base_mast_table : `~mast_table.base.BaseMastTable`
        BaseMastTable widget to display.

    on_popout_button: callable, optional
        Callback to expose popout button. Default is None.

    """
    solara.provide_cross_filter()

    pending_reducer, set_pending_reducer = solara.use_state("AND")
    filter_masks, set_filter_masks = solara.use_state({})
    filters, set_filters = solara.use_state([])
    drawer_open, set_drawer_open = solara.use_state(False)

    # get defaults for "add filter", establish pending accordingly
    default_column = table.colnames[0]
    default_opt = slide_or_select(table, default_column)
    if default_opt == "slider":
        default_value, _ = table_range(table, default_column)
    else:
        unique_values, _ = build_select_items(table[default_column])
        default_value = unique_values[0] if unique_values else ""
    default_mode = ">=" if default_opt == "slider" else "=="

    pending, set_pending = solara.use_state({
        "column": default_column,
        "value": default_value,
        "mode": default_mode,
    })
    pending_column = pending["column"]
    pending_value = pending["value"]
    pending_mode = pending["mode"]

    def set_pending_value(value):
        set_pending({
            **pending,
            "value": value,
        })

    def set_pending_mode(mode):
        set_pending({
            **pending,
            "mode": mode,
        })

    def add_filter(opt):
        new_filters = filters + [
            {
                "id": str(uuid.uuid4()),
                "column": pending_column,
                "value": pending_value,
                "mode": pending_mode if opt == "slider" else "==",
            }
        ]
        set_filters(new_filters)

        set_pending({
            "column": default_column,
            "value": default_value,
            "mode": default_mode,
        })

    def remove_filter(filter_id):
        set_filters([f for f in filters if f["id"] != filter_id])

        updated = dict(filter_masks)
        updated.pop(filter_id, None)
        set_filter_masks(updated)

    def update_filter_mode(filter_id, new_mode):
        set_filters(
            [
                {**f, "mode": new_mode} if f["id"] == filter_id else f
                for f in filters
            ]
        )

    def set_mask(filter_id, mask):
        updated = dict(filter_masks)

        if mask is None:
            updated.pop(filter_id, None)
        else:
            updated[filter_id] = mask

        set_filter_masks(updated)

    active_masks = [
        mask for mask in filter_masks.values()
        if mask is not None
    ]

    if not active_masks:
        combined_mask = None
    elif pending_reducer == "AND":
        combined_mask = functools.reduce(
            operator.and_,
            active_masks
        )
    else:
        combined_mask = functools.reduce(
            operator.or_,
            active_masks
        )

    solara.lab.theme.themes.light.primary = "#00617e"
    solara.lab.theme.themes.dark.primary = "#013b4d"
    expanded_ids, set_expanded_ids = solara.use_state(set())
    target_model_id = solara.use_reactive("")

    with solara.Column(
        classes=["mast-table-view"],
        style={
            "width": "100%",
            "min-width": "0",
        }
    ) as mast_table_view:
        solara.Style(
            """
            body.jupyter-widgets-popout-container .mast-table-view {
                width: 100vw;
                max-width: 100vw;
            }
            """
        )
        with solara.Row():
            # creating popout filters panel
            with solara.Card(
                style={
                    "display": "block" if drawer_open else "none",
                    "width": "320px",
                    "flex-shrink": "0",
                    "min-height": "420px",
                    "max-height": "550px",
                    "overflow-y": "auto",
                }
            ):
                with solara.Row(
                    style={
                        "align-items": "center",
                        "justify-content": "space-between",
                        "width": "100%",
                        "padding": 0,
                    }
                ):
                    solara.Markdown(
                        "##Active filters",
                        style={
                            "margin": "0",
                            "padding": "0",
                            "line-height": "1",
                        }
                    )
                    if len(filters) > 1:
                        solara.Style(
                            """
                            .custom-toggle {
                                display: flex;
                                flex: 0 0 auto;
                                width: 100px;
                                min-width: 100px;
                                overflow: hidden;
                                margin: 0;
                                padding: 0;
                            }
                            .custom-toggle .v-btn {
                                background-color: #F2F2F2;
                                color: light-dark(#00617e, #013b4d);
                                height: 40px;
                                width: 50px;
                                min-width: 50px;
                                max-width: 50px;
                                flex: 0 0 50px;
                                margin: 0;
                                padding: 0;
                            }
                            .custom-toggle .v-btn--active {
                                background-color: light-dark(#00617e, #013b4d);
                                color: white;
                            }
                            """
                        )

                        solara.ToggleButtonsSingle(
                            value=pending_reducer,
                            values=["AND", "OR"],
                            on_value=set_pending_reducer,
                            classes=["custom-toggle"],
                        )

                        solara.Style(
                            """
                            .reset-button {
                                min-width: 0px;
                                width: 40px;
                                height: 40px;
                                padding: 0;
                                transform: translateY(-4px);
                            }
                            """
                        )

                        with solara.Tooltip("Remove all active filters"):
                            solara.Button(
                                icon_name="mdi-refresh",
                                on_click=lambda *args: (set_filters([]), set_filter_masks({})),
                                style={
                                    "background-color": "light-dark(#00617e, #013b4d)",
                                    "color": "white"
                                },
                                classes=["reset-button"]
                            )

                # creating slide/select for each active filter
                for f in filters:
                    with solara.Row(style={"width": "100%"}):
                        solara.Style(
                            """
                            .filter-card .v-card {
                                padding: 0;
                            }
                            .filter-card .v-card-text {
                                padding: 4px 8px;
                            }
                            .filter-card .v-card-actions {
                                padding: 0px 8px;
                            }
                            """
                        )

                        with solara.Card(
                            classes=["filter-card"],
                            style={
                                "border": "2px solid light-dark(#00617e, #013b4d)",
                                "box-shadow": "none",
                                "width": "100%",
                            }
                        ):
                            opt = slide_or_select(table, f["column"])
                            initial_val = f["value"] if f.get("value") is not None else None

                            is_expanded = f["id"] in expanded_ids

                            def toggle(filter_id=f["id"]):
                                ids = set(expanded_ids)
                                if filter_id in ids:
                                    ids.remove(filter_id)
                                else:
                                    ids.add(filter_id)
                                set_expanded_ids(ids)

                            with solara.Row(
                                style={
                                    "align-items": "center",
                                    "justify-content": "space-between",
                                    "width": "100%",
                                    "padding": 0,
                                }
                            ):
                                solara.Style(
                                    """
                                    .v-btn.filter-column {
                                        text-transform: none;
                                        font-family: inherit;
                                        font-size: inherit;
                                        font-weight: bold;
                                        letter-spacing: normal;
                                    }
                                    .filter-column {
                                        min-width: 0;
                                        flex: 1 1 auto;
                                    }
                                    .filter-column .v-btn__content {
                                        min-width: 0;
                                        max-width: 100%;
                                        overflow-x: auto;
                                        overflow-y: hidden;
                                        white-space: nowrap;
                                        display: block;
                                    }
                                    """
                                )

                                label = f'{f["column"]} {f["mode"]}'

                                solara.Button(
                                    label=label,
                                    on_click=toggle,
                                    icon_name=(
                                        "mdi-chevron-up" if is_expanded
                                        else "mdi-chevron-down"
                                    ),
                                    text=True,
                                    classes=["filter-column"],
                                    style={
                                        "margin-left": "-8px",
                                        "justify-content": "flex-start",
                                        "text-align": "left",
                                        "padding-left": "8px",
                                        "padding-right": "8px",
                                        "min-width": "0",
                                        "flex-grow": "1",
                                    },
                                )

                                with solara.Div():
                                    RemoveFilterButton(f["id"], remove_filter)

                            with solara.Div(
                                style={
                                    "display": "block" if is_expanded else "none"
                                }
                            ):
                                filter_id = f["id"]

                                def on_mode_change(new_mode, filter_id=filter_id):
                                    update_filter_mode(filter_id, new_mode)

                                if opt == "slider":
                                    CrossFilterSlider(
                                        table,
                                        f["column"],
                                        filter_id=filter_id,
                                        set_mask=set_mask,
                                        set_filter_mode=on_mode_change,
                                        mode=f["mode"],
                                        initial_value=initial_val,
                                    )
                                else:
                                    other_masks = [
                                        mask
                                        for fid, mask in filter_masks.items()
                                        if fid != filter_id and mask is not None
                                    ]

                                    if not other_masks:
                                        table_filtered = table
                                    elif pending_reducer == "AND":
                                        table_filtered = table[
                                            functools.reduce(
                                                operator.and_,
                                                other_masks
                                            )
                                        ]
                                    else:
                                        table_filtered = table[
                                            functools.reduce(
                                                operator.or_,
                                                other_masks
                                            )
                                        ]

                                    CrossFilterSelect(
                                        table,
                                        f["column"],
                                        filter_id=filter_id,
                                        set_mask=set_mask,
                                        set_filter_mode=on_mode_change,
                                        initial_values=initial_val,
                                        table_filtered=table_filtered
                                    )

                if not len(filters):
                    solara.Markdown("No active filters")

                # creating add filter section
                solara.Markdown("##Add filter")

                column_names = table.colnames
                column_names.sort(key=str.casefold)
                if col_unique_row_index in column_names:
                    # never give the internal unique column as an option
                    column_names.remove(col_unique_row_index)

                # handling pending val initialization when col changes
                def on_pending_column_change(column):
                    opt = slide_or_select(table, column)

                    if opt == "slider":
                        value, _ = table_range(table, column)
                    else:
                        unique_values, _ = build_select_items(table[column])
                        value = unique_values[0] if unique_values else ""

                    set_pending({
                        "column": column,
                        "value": value,
                        "mode": ">=" if opt == "slider" else "==",
                    })

                v.Autocomplete(
                    label="Column",
                    items=column_names,
                    v_model=pending_column,
                    on_v_model=on_pending_column_change,
                    density="compact",
                    bg_color="transparent",
                    item_color="light-dark(#00617e, #013b4d)"
                )

                opt = slide_or_select(table, pending_column)
                fully_masked = False

                # creating slide/select based on column user selects
                if opt == "slider":
                    with solara.Row(
                        style={
                            "align-items": "center",
                            "gap": "8px",
                            "flex-wrap": "wrap",
                        }
                    ):
                        solara.Text(
                            "Operator",
                            style={"margin": "0", "padding": "0"}
                        )

                        FilterModeButtons(
                            mode=pending_mode,
                            set_mode=set_pending_mode,
                        )

                    vmin, vmax = table_range(table, pending_column)

                    solara.Text(
                        f"{pending_column} {pending_mode}",
                        style={"margin": "0", "padding": "0"},
                    )

                    table_filtered = table[
                        combined_mask
                    ] if combined_mask is not None else table
                    comparison = operator_map[pending_mode]
                    slider_mask = comparison(table_filtered[pending_column], pending_value)

                    slider_args = {
                        "label": "",
                        "min": vmin,
                        "max": vmax,
                        "step": step_size(vmin, vmax),
                        "thumb_label": False,
                        "tick_labels": False,
                        "color": "primary",
                    }

                    with solara.Row(
                        style={
                            "display": "flex",
                            "alignItems": "bottom"
                        },
                        classes=["crossfilter-slider"]
                    ):
                        Input.element(
                            value=pending_value,
                            on_value=set_pending_value,
                            **slider_args,
                        )

                        v.Slider(
                            v_model=pending_value,
                            on_v_model=set_pending_value,
                            **slider_args
                        )

                    with solara.Row(
                        style={
                            "width": "100%",
                            "justify-content": "flex-end",
                            "margin": "0",
                            "padding": "0",
                        }
                    ):
                        solara.Text(
                            (
                                f"{len(table_filtered[slider_mask])} of "
                                f"{len(table_filtered)} after filtering"
                            ),
                            style={
                                "font-size": "12px",
                                "margin": "0",
                                "padding": "0",
                            },
                        )
                else:
                    unique_values, fully_masked = build_select_items(
                        table[pending_column]
                    )

                    table_filtered = table[combined_mask] if combined_mask is not None else None

                    max_unique = 100

                    items, value_counts = build_select_filter_preview(
                        table,
                        pending_column,
                        max_unique=max_unique,
                        table_filtered=table_filtered,
                    )

                    if pending_value not in ("", None):
                        value = next(
                            (item for item in items if item["value"] == pending_value),
                            None,
                        )
                    else:
                        value = None

                    def set_pending_select_value(selection):
                        if selection is None:
                            set_pending_value("")
                        else:
                            set_pending_value(selection["value"])

                    Select.element(
                        value=value,
                        items=items,
                        on_value=set_pending_select_value,
                        label="Value",
                        clearable=False,
                        return_object=True,
                        multiple=False,
                        filtered=pending_value is not None,
                        count=len(table_filtered) if table_filtered is not None else len(table),
                    )

                    if len(value_counts) > max_unique:
                        Alert.element(
                            text=(
                                f"{pending_column} has {len(value_counts)} unique values. "
                                f"Showing the first {max_unique}."
                            ),
                            icon="mdi-information"
                        )

                with solara.Row(justify="end"):
                    solara.Button(
                        label="Apply filter",
                        icon_name="mdi-plus",
                        on_click=lambda *args: add_filter(opt),
                        disabled=fully_masked,
                        style={"background-color": "light-dark(#00617e, #013b4d)", "color": "white"}
                    )
                if fully_masked:
                    with solara.Row(justify="end"):
                        solara.Markdown("(Column fully masked)")

            with solara.Column(style="flex: 1; overflow: auto; min-height: 0"):
                filtered_table = (
                    table[combined_mask]
                    if combined_mask is not None
                    else table
                )

                # prevent circular import:
                from mast_table.mast_table import SelectableTable

                SelectableTable(
                    filtered_table,
                    base_mast_table,
                    drawer_open=drawer_open,
                    set_drawer_open=set_drawer_open,
                )
                # Popout button overlays the BaseMastTable
                if target_model_id.value:
                    solara.Style(
                        """
                        .popout-button {
                            position: relative;
                        }

                        .popout-button::after {
                            content: "Display in a new window";
                            position: absolute;
                            top: calc(100% + 6px);
                            right: 0;
                            padding: 6px 10px;
                            background-color: #424242;
                            color: white;
                            border-radius: 4px;
                            font-size: 14px;
                            white-space: nowrap;
                            opacity: 0;
                            visibility: hidden;
                            pointer-events: none;
                            z-index: 10000;
                        }

                        .popout-button:hover::after {
                            opacity: 1;
                            visibility: visible;
                        }
                        """
                    )
                    with solara.Column(
                        classes=["popout-button"],
                        style={
                            "position": "absolute",
                            "top": "25px",
                            "right": "10px",
                            "z-index": "1000",
                        }
                    ):
                        PopoutButton.element(
                            target_model_id=target_model_id.value,
                            window_features="popup,width=1200,height=600",
                        )

    def set_popout():
        mast_table_widget = solara.get_widget(mast_table_view)
        target_model_id.set(mast_table_widget._model_id)

        popout_button = PopoutButton(
            target=mast_table_widget,
            window_features="popup,width=1200,height=600",
        )

        if on_popout_button is not None:
            on_popout_button(popout_button)

    solara.use_effect(set_popout)
