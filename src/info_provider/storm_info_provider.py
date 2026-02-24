import logging
import sys

from info_provider.glue.glue2 import Glue2
from info_provider.storm_space_info_builder import SpaceInfoBuilder
from info_provider.utils.ldap_utils import LDIFExporter


class StormInfoProvider:
    def __init__(self, **args):
        logging.debug("StormInfoProvider initialization ...")
        # set configuration
        if not args.get("configuration"):
            raise ValueError("No configuration provided")
        self._configuration = args["configuration"]
        # set Glue2
        if not args.get("glue2"):
            self._glue2 = Glue2(self._configuration)
        else:
            self._glue2 = args["glue2"]

    def configure(self):
        logging.debug("Configure ...")
        # load space info
        spaceinfo = SpaceInfoBuilder(self._configuration).build()
        # configure Glue2 info
        self._glue2.configure(spaceinfo)
        return

    def get_static_ldif(self):
        logging.debug("Get static LDIF ...")

        # load space info
        spaceinfo = SpaceInfoBuilder(self._configuration).build()

        exporter = LDIFExporter()

        # get Glue2 static LDIF info
        exporter.add_nodes(self._glue2.get_static_ldif_nodes(spaceinfo))

        exporter.print_nodes(sys.stdout)
        return

    def get_update_ldif(self):
        logging.debug("Get update LDIF ...")

        # check serving state
        serving_state = self._configuration.get_serving_state()

        # load space info
        spaceinfo = SpaceInfoBuilder(self._configuration).build()

        exporter = LDIFExporter()

        # get Glue2 update LDIF info
        exporter.add_nodes(self._glue2.get_update_ldif_endpoints(serving_state))
        exporter.add_nodes(
            self._glue2.get_update_ldif_spaceinfo(spaceinfo, serving_state)
        )

        exporter.print_nodes(sys.stdout)
        return
