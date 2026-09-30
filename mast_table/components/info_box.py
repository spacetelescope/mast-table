from ipyvuetify import VuetifyTemplate
import traitlets


class InfoBox(VuetifyTemplate):
    template_file = __file__, "info_box.vue"

    text = traitlets.Any(allow_none=True).tag(sync=True)
    icon = traitlets.Any(allow_none=True).tag(sync=True)