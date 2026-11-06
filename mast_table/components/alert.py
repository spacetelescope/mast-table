from ipyvuetify import VuetifyTemplate
import traitlets


class Alert(VuetifyTemplate):
    """
    Alert vue component.

    Parameters
    ----------
    text : `traitlets.Any`
        Text content of the alert
    icon : `traitlets.Any`
        Icon to accompany the alert
    """

    template_file = __file__, "alert.vue"

    text = traitlets.Any(allow_none=True).tag(sync=True)
    icon = traitlets.Any(allow_none=True).tag(sync=True)
