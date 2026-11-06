from ipyvuetify import VuetifyTemplate
import traitlets


class Input(VuetifyTemplate):
    """
    Input vue component.

    Parameters
    ----------
    value : `traitlets.Any`
        Value of the input.
    min : `traitlets.Float`
        Smallest value
    max : `traitlets.Float`
        Largest value
    step : `traitlets.Float`
        Incremements between ``min`` and ``max``.
    """
    template_file = __file__, "cross_filter_input.vue"

    value = traitlets.Any(allow_none=True).tag(sync=True)
    min = traitlets.Float().tag(sync=True)
    max = traitlets.Float().tag(sync=True)
    step = traitlets.Float().tag(sync=True)
