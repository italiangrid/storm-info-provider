import logging
import os
import re

from .configuration import Configuration
from .glue import *
from .glue13data import *
from .utils import round_div,delete_files

class Glue13(Glue):

    FROM_BYTES_TO_GB = 1000000000
    FROM_BYTES_TO_KB = 1000

    GLUE13_INFO_SERVICE = GlueConstants.INFO_SERVICE_SCRIPT + "/glite-info-service"
    GLUE13_SERVICE_FILE = GlueConstants.INFO_PROVIDER_PATH + "/service-srm-storm-v2"
    GLUE13_SERVICE_CONFIG_FILE = GlueConstants.INFO_SERVICE_CONFIG + "/glite-info-service-srm-storm-v2.conf"
    GLUE13_STATIC_LDIF_FILE = GlueConstants.INFO_LDIF_PATH + "/static-file-storm.ldif"
    GLUE13_INFO_PLUGIN_FILE = GlueConstants.INFO_PLUGIN_PATH + "/glite-info-dynamic-storm"

    def __init__(self):
        self.access_protocols_streams = { 
            'file': {
                'version': '1.0.0',
                'maxstreams': '1'
                },
            'rfio': {
                'version': '1.0.0',
                'maxstreams': '1'
                },
            'gsiftp': {
                'version': '2.0.0',
                'maxstreams': '10'
                }, 
            'root': {
                'version': '1.0.0',
                'maxstreams': '1'
                }, 
            'http': {
                'version': '1.1.0',
                'maxstreams': '1'
                }, 
            'https': {
                'version': '1.1.0',
                'maxstreams': '1'
                }
        }
        return

    def init(self, configuration, stats):
        # GLUE13_SERVICE_FILE
        logging.debug("Creating %s ...", self.GLUE13_SERVICE_FILE)
        self.create_service_file(configuration)
        logging.info("Successfully created %s !", self.GLUE13_SERVICE_FILE)
        # GLUE13_SERVICE_CONFIG_FILE
        logging.debug("Creating %s ...", self.GLUE13_SERVICE_CONFIG_FILE)
        self.create_service_config_file(configuration, stats)
        logging.info("Successfully created %s !", self.GLUE13_SERVICE_CONFIG_FILE)
        # GLUE13_STATIC_LDIF_FILE
        logging.debug("Creating %s ...", self.GLUE13_STATIC_LDIF_FILE)
        self.create_static_ldif_file(configuration, stats)
        logging.info("Successfully created %s !", self.GLUE13_STATIC_LDIF_FILE)
        # GLUE13_PLUGIN_FILE
        logging.debug("Creating %s ...", self.GLUE13_INFO_PLUGIN_FILE)
        self.create_plugin_file()
        logging.info("Successfully created %s !", self.GLUE13_INFO_PLUGIN_FILE)
        # remove old cron file
        self.remove_old_cron_file_if_exists()
        return

    def update(self, configuration, stats):
        # generates the updater node list
        nodes = self.get_update_nodes(configuration, stats)
        # print LDIF
        return super(Glue13, self).print_update_ldif(nodes)

    def create_service_file(self, configuration):
        params = []
        params.append(configuration.get('SITE_NAME'))
        params.append(configuration.get_public_srm_endpoint())   
        return super(Glue13, self).create_service_file(self.GLUE13_SERVICE_FILE, self.GLUE13_INFO_SERVICE, self.GLUE13_SERVICE_CONFIG_FILE, params)

    def create_service_config_file(self, configuration, stats):
        content = self.get_service_configuration(configuration, stats.get_managed_vos())
        return super(Glue13, self).create_service_config_file(self.GLUE13_SERVICE_CONFIG_FILE, content)

    def create_plugin_file(self):
        params = ["/etc/storm/backend-server/storm-yaim-variables.conf"]
        info_service = "/usr/libexec/storm-dynamic-info-provider/glite-info-dynamic-storm"
        return super(Glue13, self).create_plugin_file(self.GLUE13_INFO_PLUGIN_FILE, info_service, params)

    def create_static_ldif_file(self, configuration, stats):
        # list of (dn, entries)
        nodes = []
        # common variables
        GlueSiteUniqueID = configuration.get("SITE_NAME")
        GlueSEUniqueID = configuration.get("STORM_FRONTEND_PUBLIC_HOST")

        # GlueSE
        node = GlueSE(GlueSEUniqueID)
        node.init_as_default().add({
            'GlueSEUniqueID': [GlueSEUniqueID],
            'GlueSEName': [configuration.get("SITE_NAME") + ":srm_v2"],
            'GlueSESizeTotal': [str(round_div(stats.get_summary()["total-space"],self.FROM_BYTES_TO_GB) + round_div(stats.get_summary()["nearline-space"],self.FROM_BYTES_TO_GB))],
            'GlueSESizeFree': [str(round_div(stats.get_summary()["free-space"],self.FROM_BYTES_TO_GB))],
            'GlueSETotalOnlineSize': [str(round_div(stats.get_summary()["total-space"],self.FROM_BYTES_TO_GB))],
            'GlueSEUsedOnlineSize': [str(round_div(stats.get_summary()["used-space"],self.FROM_BYTES_TO_GB))],
            'GlueSETotalNearlineSize': [str(round_div(stats.get_summary()["nearline-space"],self.FROM_BYTES_TO_GB))],
            'GlueInformationServiceURL': ["ldap://" + configuration.get("STORM_BACKEND_HOST") + ":2170/mds-vo-name=resource,o=grid"],
            'GlueForeignKey': [ "GlueSiteUniqueID=" + GlueSiteUniqueID]
        })
        nodes.append(node)

        # for each storage area / virtual file system
        for sa_name,sa_data in stats.get_vfs().items():
            # GlueSA
            GlueSALocalID = ":".join((sa_name, sa_data["retentionPolicy"], sa_data["accessLatency"]))
            node = GlueSALocal(GlueSALocalID, GlueSEUniqueID)
            node.init_as_default().add({
                'GlueSALocalID': [GlueSALocalID],
                'GlueSATotalOnlineSize': [str(round_div(sa_data["total-space"], self.FROM_BYTES_TO_GB))], # total space in GB
                'GlueSAUsedOnlineSize': [str(round_div(sa_data["used-space"], self.FROM_BYTES_TO_GB))], # used space in GB
                'GlueSAFreeOnlineSize': [str(round_div(sa_data["free-space"], self.FROM_BYTES_TO_GB))], # free space in GB
                'GlueSAReservedOnlineSize': [str(round_div(sa_data["total-space"], self.FROM_BYTES_TO_GB))], # reserved = total in prev bash script for Glue1.3
                'GlueSATotalNearlineSize': [str(round_div(sa_data["availableNearlineSpace"], self.FROM_BYTES_TO_GB))], # nearline size in GB
                'GlueSARetentionPolicy': [str(sa_data["retentionPolicy"])],
                'GlueSAStateAvailableSpace': [str(round_div(sa_data["available-space"], self.FROM_BYTES_TO_KB))], # available space in KB
                'GlueSAStateUsedSpace': [str(round_div(sa_data["used-space"], self.FROM_BYTES_TO_KB))], # used space in KB
                'GlueSACapability': ["InstalledOnlineCapacity=" + str(round_div(sa_data["total-space"], self.FROM_BYTES_TO_GB)), 
                    "InstalledNearlineCapacity=" + str(round_div(sa_data["availableNearlineSpace"], self.FROM_BYTES_TO_GB))],
                'GlueSAAccessControlBaseRule': ["VO:" + sa_data["voname"]],
                'GlueChunkKey': ["GlueSEUniqueID=" + GlueSEUniqueID]
                })
            if self.is_VO(sa_data["voname"]):
                node.add({ 'GlueSAName': ["Reserved space for " + sa_data["voname"] + " VO"] })
            else:
                node.add({ 'GlueSAName': ["Custom space for non-VO users"] })
            nodes.append(node)

            if self.is_VO(sa_data["voname"]):
                # GlueVOInfoLocal
                GlueVOInfoLocalID = ":".join((sa_data["voname"],sa_data["token"]))
                node = GlueSAVOInfoLocal(GlueVOInfoLocalID, GlueSALocalID, GlueSEUniqueID)
                node.init_as_default().add({
                    'GlueVOInfoLocalID': [GlueVOInfoLocalID],
                    'GlueVOInfoPath': [sa_data["stfnRoot"][0]],
                    'GlueVOInfoTag': [sa_data["token"]],
                    'GlueVOInfoAccessControlBaseRule': ["VO:" + sa_data["voname"]],
                    'GlueChunkKey': ["GlueSALocalID=" + GlueSALocalID, "GlueSEUniqueID=" + GlueSEUniqueID]
                    })
                nodes.append(node)

        # GlueSEControlProtocol
        GlueSEControlProtocolLocalID = 'srm_v2.2'
        node = GlueSEControlProtocol(GlueSEControlProtocolLocalID, GlueSEUniqueID)
        node.init_as_default().add({
            'GlueSEControlProtocolLocalID': [GlueSEControlProtocolLocalID],
            'GlueSEControlProtocolType': ['SRM'],
            'GlueSEControlProtocolVersion': ['2.2.0'],
            'GlueSEControlProtocolEndpoint': [configuration.get_public_srm_endpoint()],
            'GlueChunkKey': [ "GlueSEUniqueID=" + GlueSEUniqueID]
        })
        nodes.append(node)

        # GlueSEAccessProtocol for each protocol
        enabled_prot = self.get_enabled_protocols(configuration)
        for protocol, data in enabled_prot.items():
            node = GlueSEAccessProtocol(protocol, GlueSEUniqueID)
            node.init_as_default().add({
                'GlueSEAccessProtocolLocalID': [protocol],
                'GlueSEAccessProtocolType': [protocol],
                'GlueSEAccessProtocolVersion': [data['version']],
                'GlueSEAccessProtocolMaxStreams': [data['maxstreams']],
                'GlueChunkKey': ["GlueSEUniqueID=" + GlueSEUniqueID] 
            })
            nodes.append(node)

        # remove old backup files
        self.delete_backup_files()
        # create LDIF file
        return super(Glue13, self).create_static_ldif_file(self.GLUE13_STATIC_LDIF_FILE, nodes, configuration.is_info_overwrite())

    def get_update_nodes(self, configuration, stats):
        # node list
        nodes = []
        # commons
        GlueSiteUniqueID = configuration.get("SITE_NAME")
        GlueSEUniqueID = configuration.get("STORM_FRONTEND_PUBLIC_HOST")

        # GlueSE
        node = GlueSE(GlueSEUniqueID)
        node.add({
            'GlueSESizeTotal': [str(round_div(stats.get_summary()["total-space"],self.FROM_BYTES_TO_GB) + round_div(stats.get_summary()["nearline-space"],self.FROM_BYTES_TO_GB))],
            'GlueSESizeFree': [str(round_div(stats.get_summary()["free-space"],self.FROM_BYTES_TO_GB))],
            'GlueSETotalOnlineSize': [str(round_div(stats.get_summary()["total-space"],self.FROM_BYTES_TO_GB))],
            'GlueSEUsedOnlineSize': [str(round_div(stats.get_summary()["used-space"],self.FROM_BYTES_TO_GB))],
            'GlueSETotalNearlineSize': [str(round_div(stats.get_summary()["nearline-space"],self.FROM_BYTES_TO_GB))],
            'GlueSEUsedNearlineSize': ["0"]
        })
        nodes.append(node)

        for sa_name,sa_data in stats.get_vfs().items():
            # GlueSA
            GlueSALocalID = ":".join((sa_name, sa_data["retentionPolicy"], sa_data["accessLatency"]))
            node = GlueSALocal(GlueSALocalID, GlueSEUniqueID)
            node.add({
                'GlueSATotalOnlineSize': [str(round_div(sa_data["total-space"],self.FROM_BYTES_TO_GB))], # total space in GB
                'GlueSAUsedOnlineSize': [str(round_div(sa_data["used-space"],self.FROM_BYTES_TO_GB))], # used space in GB
                'GlueSAFreeOnlineSize': [str(round_div(sa_data["free-space"],self.FROM_BYTES_TO_GB))], # free space in GB
                'GlueSAReservedOnlineSize': [str(round_div(sa_data["total-space"],self.FROM_BYTES_TO_GB))], # reserved = total in prev bash script for Glue1.3
                'GlueSATotalNearlineSize': [str(round_div(sa_data["availableNearlineSpace"],self.FROM_BYTES_TO_GB))], # nearline size in GB
                'GlueSAUsedNearlineSize': ['0'],
                'GlueSAFreeNearlineSize': ['0'],
                'GlueSAReservedNearlineSize': ['0'],
                'GlueSAStateAvailableSpace': [str(round_div(sa_data["available-space"],self.FROM_BYTES_TO_KB))], # available space in KB
                'GlueSAStateUsedSpace': [str(round_div(sa_data["used-space"],self.FROM_BYTES_TO_KB))] # used space in KB
            })
            nodes.append(node)

        return nodes

    def delete_backup_files(self):
        directory = os.path.dirname(self.GLUE13_STATIC_LDIF_FILE)
        removed_list = delete_files(directory, r'static-file-storm\.ldif\.bkp_.*')
        logging.debug("Removed backup files: [%s]", removed_list)
        return        

    def remove_old_cron_file_if_exists(self):
        cFile = "/etc/cron.d/glite-info-dynamic-storm"
        if os.path.isfile(cFile):
            os.remove(cFile)
        return

    def get_service_configuration(self, configuration, vos):

        gLite_IS_version = "2.2.0"
        gLite_IS_endpoint = configuration.get_public_srm_endpoint()
        init_command = "/usr/libexec/storm-info-provider/storm-info-provider init-env --version " + gLite_IS_version + " --endpoint " + gLite_IS_endpoint
        status_command = GlueConstants.INFO_SERVICE_SCRIPT + "/glite-info-service-test SRM_V2 && /usr/libexec/storm-info-provider/storm-info-provider status"
        get_owner = "echo " + "; echo ".join(vos)
        get_acbr = "echo VO:" + "; echo VO:".join(vos)
        content = {
            "init": init_command,
            "service_type": "SRM",
            "get_version": "echo \"" + gLite_IS_version + "\"",
            "get_endpoint": "echo \"" + gLite_IS_endpoint + "\"",
            "WSDL_URL": "http://sdm.lbl.gov/srm-wg/srm.v2.2.wsdl",
            "semantics_URL": "http://sdm.lbl.gov/srm-wg/doc/SRM.v2.2.html",
            "get_starttime": "perl -e '@st=stat(\"/var/run/storm-backend-server.pid\");print \"@st[10]\\n\";'",
            "get_data": "echo",
            "get_services": "echo",
            "get_status": status_command,
            "get_owner": get_owner,
            "get_acbr": get_acbr
        }
        return content

    def get_enabled_protocols(self, configuration):
        enabled = {}
        for protocol in configuration.get_enabled_protocols():
            enabled[protocol] = self.access_protocols_streams[protocol]
        return enabled

    def is_VO(self, VO):
        return not '*' in VO
