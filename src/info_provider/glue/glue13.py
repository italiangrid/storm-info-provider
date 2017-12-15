import logging
import os
import re
from info_provider.glue.glue13_constants import GLUE13_INFO_SERVICE_CONFIG_FILE,\
    GLUE13_INFO_PROVIDER_FILE, GLUE13_INFO_PLUGIN_FILE,\
    GLUE13_INFO_STATIC_LDIF_FILE, GLUE13_INFO_SERVICE_CONFIG_FILE_TEMPLATE,\
    GLUE13_BASEDN, GLUE13_ACCESS_PROTOCOLS
from info_provider.glue.utils import set_owner, create_file_from_template,\
    as_gigabytes, as_kilobytes
from info_provider.utils.ldap_utils import LDIFExporter
from info_provider.glue.commons import INFO_PROVIDER_SCRIPT,\
    INPUT_YAIM_CONFIGURATION
from info_provider.glue.glue13_schema import GlueSE, GlueSALocal,\
    GlueSAVOInfoLocal, GlueSEControlProtocol, GlueSEAccessProtocol



class Glue13:

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
        # remove old static LDIF backup files
        self._delete_backup_files()
        # create Glue13 service configuration file
        logging.debug("Creating %s ...", GLUE13_INFO_SERVICE_CONFIG_FILE)
        self._create_service_config_file()
        logging.info("Successfully created %s !", GLUE13_INFO_SERVICE_CONFIG_FILE)
        # create Glue13 service provider file
        logging.debug("Creating %s ...", GLUE13_INFO_PROVIDER_FILE)
        self._create_service_provider_file()
        logging.info("Successfully created %s !", GLUE13_INFO_PROVIDER_FILE)
        # create Glue13 service plug-in file
        logging.debug("Creating %s ...", GLUE13_INFO_PLUGIN_FILE)
        self._create_plugin_file()
        logging.info("Successfully created %s !", GLUE13_INFO_PLUGIN_FILE)
        # create Glue13 static LDIF file
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
        set_owner("ldap", GLUE13_INFO_PROVIDER_FILE)
        os.chmod(GLUE13_INFO_PROVIDER_FILE, 0755)
        return

    def _create_service_config_file(self):
        vos = self._configuration.get_used_VOs()
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
        set_owner("ldap", GLUE13_INFO_PLUGIN_FILE)
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
            'GlueSEName': self._configuration.get_sitename() + ":srm_v2",
            'GlueSESizeTotal': 
                as_gigabytes(spaceinfo.get_summary().get_total()) + 
                as_gigabytes(spaceinfo.get_summary().get_nearline()),
            'GlueSESizeFree': as_gigabytes(spaceinfo.get_summary().get_free()),
            'GlueSETotalOnlineSize': as_gigabytes(spaceinfo.get_summary().get_total()),
            'GlueSEUsedOnlineSize': as_gigabytes(spaceinfo.get_summary().get_used()),
            'GlueSETotalNearlineSize': as_gigabytes(spaceinfo.get_summary().get_nearline()),
            'GlueSEImplementationVersion': self._get_implementation_version(),
            'GlueInformationServiceURL': "ldap://" + 
                self._configuration.get_backend_hostname() + ":2170/" + 
                GLUE13_BASEDN,
            'GlueForeignKey':  "GlueSiteUniqueID=" + self._get_site_id()
        })
        nodes.append(node)
        logging.debug(node)

        # for each storage area / virtual file system
        for n, d in spaceinfo.get_vfs().iteritems():
            # GlueSA
            GlueSALocalID = self._get_sa_local_id(n, d.get_retentionpolicy(), d.get_accesslatency())
            node = GlueSALocal(GlueSALocalID, GlueSEUniqueID)
            node.init().add({
                'GlueSAPath': str(d.get_root()),
                'GlueSATotalOnlineSize': as_gigabytes(d.get_space().get_total()),
                'GlueSAUsedOnlineSize': as_gigabytes(d.get_space().get_used()),
                'GlueSAFreeOnlineSize': as_gigabytes(d.get_space().get_free()),
                # reserved-space = total-space in prev bash script for Glue1.3
                'GlueSAReservedOnlineSize': as_gigabytes(d.get_space().get_total()),
                'GlueSATotalNearlineSize': as_gigabytes(d.get_space().get_nearline()),
                'GlueSAFreeNearlineSize': as_gigabytes(d.get_space().get_nearline()),
                'GlueSARetentionPolicy': str(d.get_retentionpolicy()).lower(),
                'GlueSAStateAvailableSpace': as_kilobytes(d.get_space().get_available()),
                'GlueSAStateUsedSpace': as_kilobytes(d.get_space().get_used()),
                'GlueSAAccessControlBaseRule': "VO:" + str(d.get_voname()),
                'GlueSACapability': [
                    "InstalledOnlineCapacity=" + 
                        str(as_gigabytes(d.get_space().get_total())),
                    "InstalledNearlineCapacity=" + 
                        str(as_gigabytes(d.get_space().get_nearline()))
                    ]
                })
            vo_name = str(d.get_voname())
            if self.is_VO(vo_name):
                node.add({ 
                    'GlueSAName': "Reserved space for " + vo_name + " VO" 
                })
            else:
                node.add({ 
                    'GlueSAName': "Custom space for non-VO users" 
                })
            nodes.append(node)

            if self.is_VO(vo_name):
                # GlueVOInfoLocal
                GlueSAVOInfoLocalID = self._get_sa_vo_info_id(n, vo_name, d.get_token())
                node = GlueSAVOInfoLocal(GlueSAVOInfoLocalID, GlueSALocalID, GlueSEUniqueID)
                node.init().add({
                    'GlueVOInfoPath': d.get_stfnroot()[0],
                    'GlueVOInfoAccessControlBaseRule': "VO:" + vo_name
                    })
                if self._configuration.vfs_has_custom_token(n):
                    node.add({ 
                        'GlueVOInfoTag': d.get_token()
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
                as_gigabytes(spaceinfo.get_summary().get_total()) + 
                    as_gigabytes(spaceinfo.get_summary().get_nearline()),
            'GlueSESizeFree':
                as_gigabytes(spaceinfo.get_summary().get_free()),
            'GlueSETotalOnlineSize': 
                as_gigabytes(spaceinfo.get_summary().get_total()),
            'GlueSEUsedOnlineSize': 
                as_gigabytes(spaceinfo.get_summary().get_used()),
            'GlueSETotalNearlineSize': 
                as_gigabytes(spaceinfo.get_summary().get_nearline()),
            'GlueSEUsedNearlineSize': "0"
        })
        nodes.append(node)

        for sa_name, sa_data in spaceinfo.vfs.iteritems():
            # GlueSA
            GlueSALocalID = self._get_sa_local_id(sa_name, sa_data.get_retentionpolicy(), sa_data.get_accesslatency())
            node = GlueSALocal(GlueSALocalID, GlueSEUniqueID)
            node.add({
                'GlueSATotalOnlineSize':
                    as_gigabytes(sa_data.get_space().get_total()),
                'GlueSAUsedOnlineSize': 
                    as_gigabytes(sa_data.get_space().get_used()),
                'GlueSAFreeOnlineSize':
                    as_gigabytes(sa_data.get_space().get_free()),
                # reserved = total in prev bash script for Glue1.3
                'GlueSAReservedOnlineSize': 
                    as_gigabytes(sa_data.get_space().get_total()),
                'GlueSATotalNearlineSize':
                    as_gigabytes(sa_data.get_space().get_nearline()),
                'GlueSAFreeNearlineSize':
                    as_gigabytes(sa_data.get_space().get_nearline()),
                'GlueSAUsedNearlineSize': '0',
                'GlueSAReservedNearlineSize': '0',
                'GlueSAStateAvailableSpace':
                    as_kilobytes(sa_data.get_space().get_available()),
                'GlueSAStateUsedSpace':
                    as_kilobytes(sa_data.get_space().get_used())
            })
            nodes.append(node)

        return nodes

    def _delete_backup_files(self):
        parent_directory = os.path.dirname(GLUE13_INFO_STATIC_LDIF_FILE)
        removed_list = []
        for f in os.listdir(parent_directory):
            if re.search(r'storm-glue13-static\.ldif\.bkp_.*', f):
                os.remove(os.path.join(parent_directory, f))
                removed_list.append(f)
        logging.debug("Removed backup files: [%s]", removed_list)
        return len(removed_list)

    def is_VO(self, vo):
        return not '*' in vo
