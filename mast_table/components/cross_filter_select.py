from ipyvuetify import VuetifyTemplate
import traitlets
from typing import Any, Dict, List, cast


class Select(VuetifyTemplate):
    """
    Select vue component.

    Parameters
    ----------
    value : `traitlets.Any`
        Selected value
    label : `traitlets.Unicode`
        Text label
    clearable : `traitlets.Bool`
        True if the selection can be cleared
    return_object : `traitlets.Bool`
        True if the object will be returned
    items : `traitlets.List`
        List of selectable items in the Select component
    filtered : `traitlets.Bool`
        True if ``items`` is filtered
    count : `traitlets.Int`
    multiple : `traitlets.Bool`
        Allow multiselect
    messages : `traitlets.Unicode`
    search : `traitlets.Any`

    """
    template_file = __file__, "cross_filter_select.vue"

    value = traitlets.Any().tag(sync=True)
    label = traitlets.Unicode().tag(sync=True)
    clearable = traitlets.Bool().tag(sync=True)
    return_object = traitlets.Bool().tag(sync=True)
    items = traitlets.List(cast(List[Dict[str, Any]], [])).tag(sync=True)
    filtered = traitlets.Bool().tag(sync=True)
    count = traitlets.Int().tag(sync=True)
    multiple = traitlets.Bool().tag(sync=True)
    messages = traitlets.Unicode().tag(sync=True)
    search = traitlets.Any().tag(sync=True)
