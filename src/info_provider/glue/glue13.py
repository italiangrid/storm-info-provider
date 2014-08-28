import logging
import os
import re

from info_provider.glue.constants import *
from info_provider.ldap_utils import LDIFExporter
from glue13_schema import *
from utils import *



class Glue13(object):

    def __init__(self, configuration, spaceinfo):
        self._configuration = configuration
        self._stats = spaceinfo
        return

    def _get_se_id(self):
        return self._configuration.get("STORM_FRONTEND_PUBLIC_HOST")

    def _get_site_id(self):
        return self._configuration.get("SITE_NAME")

    def _get_implementation_version(self):
        return str(os.popen("rpm -q --queryformat='%{VERSION}' \
            storm-backend-server").read())

    def _get_sa_local_id(self, sa_name, retention_policy, access_latency):
        return ":".join((sa_name[:-3].lower(), retention_policy.lower(), 
            access_latency.lower()))
    
    def _get_se_control_protocol_id(self):
        return 'srm_v2.2'

    def _get_sa_vo_info_id(self, sa_name, sa_voname, sa_token):
        if self._configuration.vfs_has_custom_token(sa_name): 
            # reserved space
            return ":".join((sa_voname, sa_token))                    
        # unreserved space
        return sa_voname

    def configure(self):
        # remove old static ldif backup files
        self._delete_backup_files()
        # create Glue13 service configuration file
        logging.debug("Creating %s ...", GLUE13_INFO_SERVICE_CONFIG_FILE)
        self._create_service_config_file()
        logging.info("Successfully created %s !", 
            GLUE13_INFO_SERVICE_CONFIG_FILE)
        # create Glue13 service provider file
        logging.debug("Creating %s ...", GLUE13_INFO_PROVIDER_FILE)
        self._create_service_provider_file()
        logging.info("Successfully created %s !", GLUE13_INFO_PROVIDER_FILE)
        # create Glue13 service plugin file
        logging.debug("Creating %s ...", GLUE13_INFO_PLUGIN_FILE)
        self._create_plugin_file()
        logging.info("Successfully created %s !", GLUE13_INFO_PLUGIN_FILE)
        # create Glue13 static ldif file
        logging.debug("Creating %s ...", GLUE13_INFO_STATIC_LDIF_FILE)
        self._create_static_ldif_file()
        logging.info("Successfully created %s !", GLUE13_INFO_STATIC_LDIF_FILE)
        return

    def _create_service_provider_file(self):
        # create (overwrite) provider file
        f = open(GLUE13_INFO_PROVIDER_FILE, "w")
        f.write("#!/bin/sh\n")
        f.write("glite-info-service %s " % (GLUE13_INFO_SERVICE_CONFIG_FILE))
        f.write("%s %s" % (self._get_site_id(), 
            self._configuration.get_public_srm_endpoint()))
        f.close()
        # set ldap as owner and chmod +x
        set_owner("ldap",GLUE13_INFO_PROVIDER_FILE)
        os.chmod(GLUE13_INFO_PROVIDER_FILE, 0755)
        return

    def _create_service_config_file(self):
        vos = self._configuration.get_supported_VOs()
        params = { 
            'ENDPOINT': self._configuration.get_public_srm_endpoint(),
            'ACBR': "VO:" + "\\nVO:".join(vos),
            'OWNER': "\\n".join(vos)
        }
        create_file_from_template(
            GLUE13_INFO_SERVICE_CONFIG_FILE,
            GLUE13_INFO_SERVICE_CONFIG_FILE_TEMPLATE,
            params)
        return

    def _create_static_ldif_file(self):
        exporter = LDIFExporter()
        exporter.add_nodes(self.get_static_ldif_nodes())
        exporter.save_to_file(GLUE13_INFO_STATIC_LDIF_FILE)
        # set ldap as owner and chmod +x
        set_owner("ldap", GLUE13_INFO_STATIC_LDIF_FILE)
        return

    def _create_plugin_file(self):
        f = open(GLUE13_INFO_PLUGIN_FILE, "w")
        f.write("#!/bin/sh\n")
        f.write("%s get-update-ldif -f %s -g glue13" % (
            INFO_PROVIDER_SCRIPT, INPUT_YAIM_CONFIGURATION))
        f.close()
        # set ldap as owner and chmod +x
        set_owner("ldap",GLUE13_INFO_PLUGIN_FILE)
        os.chmod(GLUE13_INFO_PLUGIN_FILE, 0755)
        return

    def get_static_ldif_nodes(self):
        # list of (dn, entries)
        nodes = []
        
        # Commons
        GlueSEUniqueID = self._get_se_id()

        # GlueSE
        node = GlueSE(GlueSEUniqueID)
        node.init().add({
            'GlueSEName': self._configuration.get("SITE_NAME") + ":srm_v2",
            'GlueSESizeTotal': 
                self._stats.get_summary()["total-space"].as_GB() + 
                self._stats.get_summary()["nearline-space"].as_GB(),
            'GlueSESizeFree': self._stats.get_summary()["free-space"].as_GB(),
            'GlueSETotalOnlineSize': 
                self._stats.get_summary()["total-space"].as_GB(),
            'GlueSEUsedOnlineSize': 
                self._stats.get_summary()["used-space"].as_GB(),
            'GlueSETotalNearlineSize': 
                self._stats.get_summary()["nearline-space"].as_GB(),
            'GlueSEImplementationVersion': self._get_implementation_version(),
            'GlueInformationServiceURL': "ldap://" + 
                self._configuration.get("STORM_BACKEND_HOST") + ":2170/" + 
                GLUE13_BASEDN,
            'GlueForeignKey':  "GlueSiteUniqueID=" + self._get_site_id()
        })
        nodes.append(node)

        # for each storage area / virtual file system
        for sa_name,sa_data in self._stats.get_vfs().items():
            # GlueSA
            GlueSALocalID = self._get_sa_local_id(sa_name, 
                sa_data["retentionPolicy"], sa_data["accessLatency"])
            node = GlueSALocal(GlueSALocalID, GlueSEUniqueID)
            node.init().add({
                'GlueSATotalOnlineSize': 
                    sa_data["total-space"].as_GB(), # total space in GB
                'GlueSAUsedOnlineSize': 
                    sa_data["used-space"].as_GB(), # used space in GB
                'GlueSAFreeOnlineSize': 
                    sa_data["free-space"].as_GB(), # free space in GB
                'GlueSAReservedOnlineSize': 
                    sa_data["total-space"].as_GB(), # reserved = total in prev bash script for Glue1.3
                'GlueSATotalNearlineSize': sa_data["nearline-space"].as_GB(), # nearline size in GB
                'GlueSAFreeNearlineSize': sa_data["nearline-space"].as_GB(), 
                'GlueSARetentionPolicy': sa_data["retentionPolicy"].lower(),
                'GlueSAStateAvailableSpace': sa_data["available-space"].as_KB(), # available space in KB
                'GlueSAStateUsedSpace': sa_data["used-space"].as_KB(), # used space in KB
                'GlueSACapability': ["InstalledOnlineCapacity=" + str(sa_data["total-space"].as_GB()), 
                    "InstalledNearlineCapacity=" + str(sa_data["nearline-space"].as_GB())],
                'GlueSAAccessControlBaseRule': "VO:" + sa_data["voname"]
                })
            if self.is_VO(sa_data["voname"]):
                node.add({ 'GlueSAName': "Reserved space for " + sa_data["voname"] + " VO" })
            else:
                node.add({ 'GlueSAName': "Custom space for non-VO users" })
            nodes.append(node)

            if self.is_VO(sa_data["voname"]):
                # GlueVOInfoLocal
                GlueSAVOInfoLocalID = self._get_sa_vo_info_id(sa_name, sa_data["voname"], sa_data["token"])
                node = GlueSAVOInfoLocal(GlueSAVOInfoLocalID, GlueSALocalID, GlueSEUniqueID)
                node.init().add({
                    'GlueVOInfoPath': sa_data["stfnRoot"][0],
                    'GlueVOInfoAccessControlBaseRule': "VO:" + sa_data["voname"]
                    })
                if self._configuration.vfs_has_custom_token(sa_name):
                    node.add({ 'GlueVOInfoTag': sa_data["token"] })
                nodes.append(node)

        # GlueSEControlProtocol
        GlueSEControlProtocolID = self._get_se_control_protocol_id()
        node = GlueSEControlProtocol(GlueSEControlProtocolID, GlueSEUniqueID)
        node.init().add({
            'GlueSEControlProtocolEndpoint': self._configuration.get_public_srm_endpoint()
        })
        nodes.append(node)

        # GlueSEAccessProtocol for each enabled protocol
        for protocol in self._configuration.get_enabled_access_protocols():
            node = GlueSEAccessProtocol(protocol, GlueSEUniqueID)
            node.init().add({
                'GlueSEAccessProtocolVersion': GLUE13_ACCESS_PROTOCOLS[protocol]['version'],
                'GlueSEAccessProtocolMaxStreams': GLUE13_ACCESS_PROTOCOLS[protocol]['maxstreams']
            })
            nodes.append(node)

        return nodes

    def get_update_ldif_nodes(self):
        # node list
        nodes = []
        # commons
        GlueSEUniqueID = self._get_se_id()

        # GlueSE
        node = GlueSE(GlueSEUniqueID)
        node.add({
            'GlueSESizeTotal': self._stats.get_summary()["total-space"].as_GB() + self._stats.get_summary()["nearline-space"].as_GB(),
            'GlueSESizeFree': self._stats.get_summary()["free-space"].as_GB(),
            'GlueSETotalOnlineSize': self._stats.get_summary()["total-space"].as_GB(),
            'GlueSEUsedOnlineSize': self._stats.get_summary()["used-space"].as_GB(),
            'GlueSETotalNearlineSize': self._stats.get_summary()["nearline-space"].as_GB(),
            'GlueSEUsedNearlineSize': "0"
        })
        nodes.append(node)

        for sa_name,sa_data in self._stats.get_vfs().items():
            # GlueSA
            GlueSALocalID = self._get_sa_local_id(sa_name, sa_data["retentionPolicy"], sa_data["accessLatency"])
            node = GlueSALocal(GlueSALocalID, GlueSEUniqueID)
            node.add({
                'GlueSATotalOnlineSize': sa_data["total-space"].as_GB(), # total space in GB
                'GlueSAUsedOnlineSize': sa_data["used-space"].as_GB(), # used space in GB
                'GlueSAFreeOnlineSize': sa_data["free-space"].as_GB(), # free space in GB
                'GlueSAReservedOnlineSize': sa_data["total-space"].as_GB(), # reserved = total in prev bash script for Glue1.3
                'GlueSATotalNearlineSize': sa_data["nearline-space"].as_GB(), # nearline size in GB
                'GlueSAFreeNearlineSize': sa_data["nearline-space"].as_GB(),
                'GlueSAUsedNearlineSize': '0',
                'GlueSAReservedNearlineSize': '0',
                'GlueSAStateAvailableSpace': sa_data["available-space"].as_KB(), # available space in KB
                'GlueSAStateUsedSpace': sa_data["used-space"].as_KB() # used space in KB
            })
            nodes.append(node)

        return nodes

    def _delete_backup_files(self):
        parent_directory = os.path.dirname(GLUE13_INFO_STATIC_LDIF_FILE)
        removed_list = []
        for f in os.listdir(parent_directory):
            if re.search(r'storm-glue13-static\.ldif\.bkp_.*',f):
                os.remove(os.path.join(parent_directory, f))
                removed_list.append(f)
        logging.debug("Removed backup files: [%s]", removed_list)
        return len(removed_list)

    def is_VO(self, VO):
        return not '*' in VO
