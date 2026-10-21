from ipyvuetify import VuetifyTemplate
import traitlets


class Alert(VuetifyTemplate):
    template_file = __file__, "alert.vue"

    text = traitlets.Any(allow_none=True).tag(sync=True)
    icon = traitlets.Any(allow_none=True).tag(sync=True)
