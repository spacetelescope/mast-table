from ipyvuetify import VuetifyTemplate
import traitlets


class Input(VuetifyTemplate):
    template_file = __file__, "cross_filter_input.vue"

    value = traitlets.Any(allow_none=True).tag(sync=True)
    min = traitlets.Float().tag(sync=True)
    max = traitlets.Float().tag(sync=True)
    step = traitlets.Float().tag(sync=True)
