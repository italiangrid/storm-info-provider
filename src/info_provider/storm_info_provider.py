import logging
import os
import sys

from info_provider.glue.glue13 import Glue13
from info_provider.glue.glue2 import Glue2
from info_provider.utils.ldap_utils import LDIFExporter
from info_provider.storm_storage_service_builder import StorageServiceBuilder
from info_provider.storm_space_info_builder import SpaceInfoBuilder
from info_provider.storm_gateway import StormGateway


class StormInfoProvider:

    BACKEND_PID_PATH = "/var/run/storm-backend-server.pid"
    GET_IMPLEMENTATION_VERSION_CMD = "rpm -q --queryformat='%{VERSION}' storm-backend-server"

    def __init__(self, **args):
        logging.debug("StormInfoProvider initialization ...")
        # set configuration
        if not args.get("configuration"):
            raise ValueError("No configuration provided")
        self._configuration = args["configuration"]
        # set gateway
        if not args.get("gateway"):
            self._gateway = StormGateway(self._configuration.get_backend_rest_endpoint())
        else:
            self._gateway = args["gateway"]
        # set Glue13
        if not args.get("glue13"):
            self._glue13 = Glue13(self._configuration)
        else:
            self._glue13 = args["glue13"]
        # set Glue2
        if not args.get("glue2"):
            self._glue2 = Glue2(self._configuration)
        else:
            self._glue2 = args["glue2"]

    def _create_json_report(self, spaceinfo, outputfilepath):
        # create report JSON
        storage_service = StorageServiceBuilder(self._configuration, spaceinfo).build()
        self._save_string_to_file(outputfilepath, storage_service.to_json())
        logging.info("Exported JSON report to %s", outputfilepath)

    def configure(self, glue_protocol, exported_json_file_path):
        logging.debug("Configure ...")
        # load space info
        spaceinfo = SpaceInfoBuilder(self._configuration, self._gateway).build()
        # configure Glue13 info
        if glue_protocol in ['glue13', 'all']:
            self._glue13.configure(spaceinfo)
        # configure Glue2 info
        if glue_protocol in ['glue2', 'all']:    
            self._glue2.configure(spaceinfo)
        # create report json
        self._create_json_report(spaceinfo, exported_json_file_path)
        return

    def get_static_ldif(self, glue_protocol):
        logging.debug("Get static LDIF ...")
        
        # load space info
        spaceinfo = SpaceInfoBuilder(self._configuration, self._gateway).build()
    
        exporter = LDIFExporter()
    
        # get Glue13 static LDIF info
        if glue_protocol in ['glue13']:
            exporter.add_nodes(self._glue13.get_static_ldif_nodes(spaceinfo))
    
        # get Glue2 static LDIF info
        if glue_protocol in ['glue2']:
            exporter.add_nodes(self._glue2.get_static_ldif_nodes(spaceinfo))
    
        exporter.print_nodes(sys.stdout)
        return

    def get_update_ldif(self, glue_protocol):
        logging.debug("Get update LDIF ...")
        
        # check serving state
        serving_state = self._configuration.get_serving_state()
        if serving_state == "closed":
            # Backend is declared not running
            logging.error("StoRM Backend is not running")
            # update endpoints serving state
            if glue_protocol in ['glue2']:
                exporter = LDIFExporter()
                exporter.add_nodes(self._glue2.get_update_ldif_endpoints(serving_state))
                exporter.print_nodes(sys.stdout)
                return
            return

        # load space info
        spaceinfo = SpaceInfoBuilder(self._configuration, self._gateway).build()

        exporter = LDIFExporter()

        # get Glue13 update LDIF info
        if glue_protocol in ['glue13']:
            exporter.add_nodes(self._glue13.get_update_ldif_nodes(spaceinfo))
    
        # get Glue2 update LDIF info
        if glue_protocol in ['glue2']:
            exporter.add_nodes(self._glue2.get_update_ldif_endpoints(serving_state))
            exporter.add_nodes(self._glue2.get_update_ldif_spaceinfo(spaceinfo, serving_state))
    
        exporter.print_nodes(sys.stdout)
        return

    def get_report_json(self, exported_json_file_path):
        logging.debug("Get report JSON ...")
        # load space info
        spaceinfo = SpaceInfoBuilder(self._configuration, self._gateway).build()
        # create report JSON
        self._create_json_report(spaceinfo, exported_json_file_path)
        return

    def _is_backend_running(self):
        logging.debug("Checking if storm-backend-server is running ...")
        return os.path.isfile(self.BACKEND_PID_PATH)
    
    def _get_current_serving_state(self):
        logging.debug("Getting serving state ...")
        if not self._is_backend_running():
            return (1, "closed")
        return (4, "production")
    
    def _get_implementation_version(self):
        return os.popen(self.GET_IMPLEMENTATION_VERSION_CMD).read()
    
    def _save_string_to_file(self, filepath, content):
        f = open(filepath, 'w')
        f.write(content)
        f.close()
        return
