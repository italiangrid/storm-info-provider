import logging
import os
import re

from info_provider.glue.constants import *
from info_provider.ldap_utils import LDIFExporter
from glue13_schema import *
from utils import *



class Glue13(object):

    def __init__(self, configuration):
        self._configuration = configuration
        return

    def _get_se_id(self):
        return self._configuration.get("STORM_FRONTEND_PUBLIC_HOST")

    def _get_site_id(self):
        return self._configuration.get("SITE_NAME")

    def _get_implementation_version(self):
        return str(os.popen("rpm -q --queryformat='%{VERSION}' \
            storm-backend-server").read())

    def _get_sa_local_id(self, sa_name, retention_policy, access_latency):
        return ":".join([str(sa_name[:-3]).lower(), 
            str(retention_policy).lower(), str(access_latency).lower()])
    
    def _get_se_control_protocol_id(self):
        return 'srm_v2.2'

    def _get_sa_vo_info_id(self, sa_name, sa_voname, sa_token):
        if self._configuration.vfs_has_custom_token(sa_name): 
            # reserved space
            return ":".join((str(sa_voname), str(sa_token)))                    
        # unreserved space
        return sa_voname

    def configure(self, spaceinfo):
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
        self._create_static_ldif_file(spaceinfo)
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

    def _create_static_ldif_file(self, spaceinfo):
        exporter = LDIFExporter()
        exporter.add_nodes(self.get_static_ldif_nodes(spaceinfo))
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

    def get_static_ldif_nodes(self, spaceinfo):
        # list of (dn, entries)
        nodes = []
        
        # Commons
        GlueSEUniqueID = self._get_se_id()

        # GlueSE
        node = GlueSE(GlueSEUniqueID)
        node.init().add({
            'GlueSEName': self._configuration.get("SITE_NAME") + ":srm_v2",
            'GlueSESizeTotal': 
                as_GB(spaceinfo.summary["total-space"]) + 
                as_GB(spaceinfo.summary["nearline-space"]),
            'GlueSESizeFree': as_GB(spaceinfo.summary["free-space"]),
            'GlueSETotalOnlineSize': as_GB(spaceinfo.summary["total-space"]),
            'GlueSEUsedOnlineSize': as_GB(spaceinfo.summary["used-space"]),
            'GlueSETotalNearlineSize': as_GB(spaceinfo.summary["nearline-space"]),
            'GlueSEImplementationVersion': self._get_implementation_version(),
            'GlueInformationServiceURL': "ldap://" + 
                self._configuration.get("STORM_BACKEND_HOST") + ":2170/" + 
                GLUE13_BASEDN,
            'GlueForeignKey':  "GlueSiteUniqueID=" + self._get_site_id()
        })
        nodes.append(node)

        # for each storage area / virtual file system
        for n,d in spaceinfo.vfs.items():
            # GlueSA
            GlueSALocalID = self._get_sa_local_id(n, d["retentionPolicy"], 
                d["accessLatency"])
            node = GlueSALocal(GlueSALocalID, GlueSEUniqueID)
            node.init().add({
                'GlueSATotalOnlineSize': as_GB(d["space"]["total-space"]),
                'GlueSAUsedOnlineSize': as_GB(d["space"]["used-space"]),
                'GlueSAFreeOnlineSize': as_GB(d["space"]["free-space"]),
                # reserved-space = total-space in prev bash script for Glue1.3
                'GlueSAReservedOnlineSize': as_GB(d["space"]["total-space"]),
                'GlueSATotalNearlineSize': as_GB(d["space"]["nearline-space"]),
                'GlueSAFreeNearlineSize': as_GB(d["space"]["nearline-space"]),
                'GlueSARetentionPolicy': str(d["retentionPolicy"]).lower(),
                'GlueSAStateAvailableSpace': as_KB(d["space"]["available-space"]),
                'GlueSAStateUsedSpace': as_KB(d["space"]["used-space"]),
                'GlueSAAccessControlBaseRule': "VO:" + str(d["voname"]),
                'GlueSACapability': [
                    "InstalledOnlineCapacity=" + 
                        str(as_GB(d["space"]["total-space"])), 
                    "InstalledNearlineCapacity=" + 
                        str(as_GB(d["space"]["nearline-space"]))
                    ]
                })
            if self.is_VO(str(d["voname"])):
                node.add({ 
                    'GlueSAName': "Reserved space for " + str(d["voname"]) + " VO" 
                })
            else:
                node.add({ 
                    'GlueSAName': "Custom space for non-VO users" 
                })
            nodes.append(node)

            if self.is_VO(d["voname"]):
                # GlueVOInfoLocal
                GlueSAVOInfoLocalID = self._get_sa_vo_info_id(n, d["voname"], 
                    d["token"])
                node = GlueSAVOInfoLocal(GlueSAVOInfoLocalID, GlueSALocalID, 
                    GlueSEUniqueID)
                node.init().add({
                    'GlueVOInfoPath': d["stfnRoot"][0],
                    'GlueVOInfoAccessControlBaseRule': "VO:" + str(d["voname"])
                    })
                if self._configuration.vfs_has_custom_token(n):
                    node.add({ 
                        'GlueVOInfoTag': d["token"] 
                    })
                nodes.append(node)

        # GlueSEControlProtocol
        GlueSEControlProtocolID = self._get_se_control_protocol_id()
        node = GlueSEControlProtocol(GlueSEControlProtocolID, GlueSEUniqueID)
        node.init().add({
            'GlueSEControlProtocolEndpoint': 
                self._configuration.get_public_srm_endpoint()
        })
        nodes.append(node)

        # GlueSEAccessProtocol for each enabled protocol
        for protocol in self._configuration.get_enabled_access_protocols():
            node = GlueSEAccessProtocol(protocol, GlueSEUniqueID)
            node.init().add({
                'GlueSEAccessProtocolVersion': 
                    GLUE13_ACCESS_PROTOCOLS[protocol]['version'],
                'GlueSEAccessProtocolMaxStreams': 
                    GLUE13_ACCESS_PROTOCOLS[protocol]['maxstreams']
            })
            nodes.append(node)

        return nodes

    def get_update_ldif_nodes(self, spaceinfo):
        # node list
        nodes = []
        # commons
        GlueSEUniqueID = self._get_se_id()

        # GlueSE
        node = GlueSE(GlueSEUniqueID)
        node.add({
            'GlueSESizeTotal': 
                as_GB(spaceinfo.summary["total-space"]) + 
                    as_GB(spaceinfo.summary["nearline-space"]),
            'GlueSESizeFree':
                as_GB(spaceinfo.summary["free-space"]),
            'GlueSETotalOnlineSize': 
                as_GB(spaceinfo.summary["total-space"]),
            'GlueSEUsedOnlineSize': 
                as_GB(spaceinfo.summary["used-space"]),
            'GlueSETotalNearlineSize': 
                as_GB(spaceinfo.summary["nearline-space"]),
            'GlueSEUsedNearlineSize': "0"
        })
        nodes.append(node)

        for sa_name,sa_data in spaceinfo.vfs.items():
            # GlueSA
            GlueSALocalID = self._get_sa_local_id(sa_name, 
                sa_data.get("retentionPolicy"), sa_data.get("accessLatency"))
            node = GlueSALocal(GlueSALocalID, GlueSEUniqueID)
            node.add({
                'GlueSATotalOnlineSize':
                    as_GB(sa_data["space"]["total-space"]),
                'GlueSAUsedOnlineSize': 
                    as_GB(sa_data["space"]["used-space"]),
                'GlueSAFreeOnlineSize':
                    as_GB(sa_data["space"]["free-space"]),
                # reserved = total in prev bash script for Glue1.3
                'GlueSAReservedOnlineSize': 
                    as_GB(sa_data["space"]["total-space"]),
                'GlueSATotalNearlineSize':
                    as_GB(sa_data["space"]["nearline-space"]),
                'GlueSAFreeNearlineSize':
                    as_GB(sa_data["space"]["nearline-space"]),
                'GlueSAUsedNearlineSize': '0',
                'GlueSAReservedNearlineSize': '0',
                'GlueSAStateAvailableSpace':
                    as_KB(sa_data["space"]["available-space"]),
                'GlueSAStateUsedSpace':
                    as_KB(sa_data["space"]["used-space"])
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
