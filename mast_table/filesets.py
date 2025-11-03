from astroquery.mast import MastMissions

from mast_table import MastTable
from mast_table.products import Products


class Filesets(MastTable):
    def send_footprints_to(self, *apps):
        if len(apps) == 1 and isinstance(apps[0], (tuple, list)):
            apps = apps[0]

        for app in apps:
            if hasattr(app, 'viewers'):
                raise NotImplementedError(
                    f"The provided app {app} does not yet have support for this feature."
                )
            elif hasattr(app, '_fov_xy'):
                app.add_table(self.table)
            else:
                raise NotImplementedError(
                    f"The provided app {app} does not yet have support for this feature."
                )

    def get_products_from_selected(self):
        MastMissions(mission=self.mission)
        products = MastMissions(mission=self.mission).get_product_list(
            self.selected_rows_table
        )
        return Products(products)
