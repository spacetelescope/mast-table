import os
from astroquery.mast import MastMissions

from mast_table import MastTable


class Products(MastTable):
    def vue_open_selected_rows_in_jdaviz(self, *args):
        from jdaviz import Imviz
        from jdaviz.configs.imviz.helper import _current_app as viz

        if viz is None:
            viz = Imviz()

        with viz.batch_load():
            for filename in self.selected_rows_table['filename']:
                _download_from_mast(filename)
                viz.load(filename)

        orientation = viz.plugins['Orientation']
        orientation.align_by = 'WCS'
        orientation.set_north_up_east_left()

        plot_options = viz.plugins['Plot Options']
        if len(plot_options.layer.choices) > 1:
            for layer in plot_options.layer.choices:
                plot_options.layer = layer
                plot_options.image_color_mode = 'Color'

            plot_options.apply_RGB_presets()

        return

    def vue_open_selected_rows_in_aladin(self, *args):
        from mast_aladin.app import gca

        mal = gca()

        for filename in self.selected_rows_table['filename']:
            _download_from_mast(filename)
            mal.delayed_add_fits(filename)

        return


def _download_from_mast(product_file_name):
    if os.path.exists(product_file_name):
        # support load from cache without query to MM
        return

    if product_file_name.startswith('jw'):
        mission = 'jwst'
    elif product_file_name.startswith('r'):
        mission = 'roman'
    else:
        mission = 'hst'

    MastMissions(mission=mission).download_file(product_file_name)
