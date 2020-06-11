import logging
import os
import re
from urlparse import urlparse

from info_provider.glue.commons import INFO_PROVIDER_SCRIPT, \
    INPUT_YAIM_CONFIGURATION
from info_provider.glue.glue2_constants import GLUE2_ACCESS_PROTOCOLS_VERSIONS, \
    GLUE2_INFO_SERVICE_CONFIG_FILE, GLUE2_INFO_SERVICE_SRM_CONFIG_FILE, \
    GLUE2_INFO_PROVIDER_FILE, GLUE2_INFO_PLUGIN_FILE, \
    GLUE2_INFO_STATIC_LDIF_FILE, GLUE2_INFO_SERVICE_CONFIG_FILE_TEMPLATE, \
    GLUE2_INFO_SERVICE_SRM_CONFIG_FILE_TEMPLATE
from info_provider.glue.glue2_schema import GLUE2StorageService, \
    GLUE2StorageServiceCapacity, GLUE2StorageAccessProtocol, GLUE2StorageManager, \
    GLUE2DataStore, GLUE2StorageShare, GLUE2MappingPolicy, \
    GLUE2StorageShareCapacity, GLUE2WebDAVStorageEndpoint, GLUE2AccessPolicy, \
    GLUE2StorageEndpoint
from info_provider.glue.utils import create_file_from_template, set_owner, as_gigabytes
from info_provider.utils.ldap_utils import LDIFExporter


class Glue2:

    def __init__(self, configuration):
        self._configuration = configuration

    def _get_access_protocol_version(self, name):
        return GLUE2_ACCESS_PROTOCOLS_VERSIONS[name]

    def _get_service_id(self):
        return self._configuration.get_backend_hostname() + "/storage"

    def _get_site_id(self):
        return self._configuration.get_sitename()

    def _get_manager_id(self):
        return self._get_service_id() + "/manager"

    def _get_srm_endpoint_id(self, index=0):
        return self._get_service_id() + "/endpoint/SRM" + str(index)

    def _get_http_endpoint_id(self, index=0):
        return self._get_service_id() + "/endpoint/HTTP" + str(index)

    def _get_https_endpoint_id(self, index=0):
        return self._get_service_id() + "/endpoint/HTTPS" + str(index)

    def _get_endpoint_policy_id(self, endpoint_id):
        return endpoint_id + "_Policy"

    def _get_service_capacity_id(self, capacity_type):
        return self._get_service_id() + "/capacity/" + capacity_type

    def _get_access_protocol_id(self, name, version):
        return self._get_service_id() + "/accessprotocol/" + name + "/" + version

    def _get_data_store_id(self, ds_type):
        return self._get_service_id() + "/datastore/" + ds_type

    def _get_share_id(self, vfs_name):
        return self._get_service_id() + "/share/" + vfs_name[:-3].lower()

    def _get_sharing_id(self, vfs_name, vfs_retention, vfs_latency):
        return ":".join((vfs_name[:-3].lower(), vfs_retention.lower(),
            vfs_latency.lower()))

    def _get_share_policy_id(self, vfs_name):
        return self._get_share_id(vfs_name) + "/mappingpolicy"

    def _get_share_capacity_id(self, vfs_name, capacity_type):
        return self._get_share_id(vfs_name) + "/capacity/" + capacity_type

    def _is_anonymous(self, voname):
        return "*" in voname

    def configure(self, spaceinfo):
        # remove old static ldif backup files
        self._delete_backup_files()
        # create Glue2 service configuration file
        logging.debug("Creating %s ...", GLUE2_INFO_SERVICE_CONFIG_FILE)
        self._create_service_config_file()
        logging.info("Successfully created %s !", GLUE2_INFO_SERVICE_CONFIG_FILE)
        # create Glue2 srm endpoint configuration file
        logging.debug("Creating %s ...", GLUE2_INFO_SERVICE_SRM_CONFIG_FILE)
        self._create_srm_endpoint_config_file()
        logging.info("Successfully created %s !", GLUE2_INFO_SERVICE_SRM_CONFIG_FILE)
        # create Glue2 service provider file
        logging.debug("Creating %s ...", GLUE2_INFO_PROVIDER_FILE)
        self._create_service_provider_file()
        logging.info("Successfully created %s !", GLUE2_INFO_PROVIDER_FILE)
        # create Glue2 service plugin file
        logging.debug("Creating %s ...", GLUE2_INFO_PLUGIN_FILE)
        self._create_plugin_file()
        logging.info("Successfully created %s !", GLUE2_INFO_PLUGIN_FILE)
        # create Glue2 static ldif file
        logging.debug("Creating %s ...", GLUE2_INFO_STATIC_LDIF_FILE)
        self._create_static_ldif_file(spaceinfo)
        logging.info("Successfully created %s !", GLUE2_INFO_STATIC_LDIF_FILE)
        return

    def _create_service_config_file(self):
        params = {
            'SITEID': self._get_site_id(),
            'SERVICEID': self._get_service_id(),
            'QUALITY_LEVEL': self._configuration.get_quality_level()
        }
        create_file_from_template(
            GLUE2_INFO_SERVICE_CONFIG_FILE,
            GLUE2_INFO_SERVICE_CONFIG_FILE_TEMPLATE,
            params)
        return

    def _create_srm_endpoint_config_file(self):
        vos = self._configuration.get_used_VOs()
        params = {
            'SITEID': self._get_site_id(),
            'ENDPOINT': self._configuration.get_public_srm_endpoint(),
            'QUALITY_LEVEL': self._configuration.get_quality_level(),
            'SERVICEID': self._get_service_id(),
            'ACBR': "VO:" + "\\nVO:".join(vos),
            'OWNER': "\\n".join(vos)
        }
        create_file_from_template(
            GLUE2_INFO_SERVICE_SRM_CONFIG_FILE,
            GLUE2_INFO_SERVICE_SRM_CONFIG_FILE_TEMPLATE,
            params)
        return

    def _create_service_provider_file(self):
        # create (overwrite) provider file
        f = open(GLUE2_INFO_PROVIDER_FILE, "w")
        f.write("#!/bin/sh\n")
        f.write("glite-info-glue2-simple ")
        f.write("%s,%s " % (GLUE2_INFO_SERVICE_SRM_CONFIG_FILE, GLUE2_INFO_SERVICE_CONFIG_FILE))
        f.write("%s " % (self._get_site_id()))
        f.write("%s " % (self._get_service_id()))
        f.write("%s\n" % (self._get_srm_endpoint_id()))
        f.close()
        # set ldap as owner and chmod +x
        set_owner("ldap", GLUE2_INFO_PROVIDER_FILE)
        os.chmod(GLUE2_INFO_PROVIDER_FILE, 0755)
        return

    def _create_plugin_file(self):
        f = open(GLUE2_INFO_PLUGIN_FILE, "w")
        f.write("#!/bin/sh\n")
        f.write("%s get-update-ldif -f %s -g glue2" % (INFO_PROVIDER_SCRIPT, INPUT_YAIM_CONFIGURATION))
        f.close()
        # set ldap as owner and chmod +x
        set_owner("ldap", GLUE2_INFO_PLUGIN_FILE)
        os.chmod(GLUE2_INFO_PLUGIN_FILE, 0755)
        return

    def _create_static_ldif_file(self, spaceinfo):
        exporter = LDIFExporter()
        exporter.add_nodes(self.get_static_ldif_nodes(spaceinfo))
        exporter.save_to_file(GLUE2_INFO_STATIC_LDIF_FILE)
        # set ldap as owner and chmod +x
        set_owner("ldap", GLUE2_INFO_STATIC_LDIF_FILE)
        return

    def get_static_ldif_nodes(self, spaceinfo):

        nodes = []
        # Commons
        service_id = self._get_service_id()
        storm_version = self._configuration.get_implementation_version()
        issuer_ca = self._configuration.get_issuer_ca()

        # Glue2StorageService
        # NOTE: It must be removed when 'storm' type will be added
        node = GLUE2StorageService(service_id)
        node.init().add({
            'GLUE2ServiceQualityLevel': self._configuration.get_quality_level(),
            'GLUE2ServiceAdminDomainForeignKey': self._get_site_id()
            })
        nodes.append(node)

        # Glue2StorageServiceCapacity online
        if spaceinfo.get_summary().has_online_capacity():
            sc_id = self._get_service_capacity_id("online")
            node = GLUE2StorageServiceCapacity(sc_id, service_id)
            node.init().add({
                'GLUE2StorageServiceCapacityType': "online",
                'GLUE2StorageServiceCapacityTotalSize':
                    as_gigabytes(spaceinfo.get_summary().get_total()),
                'GLUE2StorageServiceCapacityFreeSize':
                    as_gigabytes(spaceinfo.get_summary().get_free()),
                'GLUE2StorageServiceCapacityUsedSize':
                    as_gigabytes(spaceinfo.get_summary().get_used()),
                'GLUE2StorageServiceCapacityReservedSize':
                    as_gigabytes(spaceinfo.get_summary().get_reserved())
            })
            nodes.append(node)

        # Glue2StorageServiceCapacity near-line
        if spaceinfo.get_summary().has_nearline_capacity():
            sc_id = self._get_service_capacity_id("nearline")
            node = GLUE2StorageServiceCapacity(sc_id, service_id)
            node.init().add({
                'GLUE2StorageServiceCapacityType': "nearline",
                'GLUE2StorageServiceCapacityTotalSize':
                    as_gigabytes(spaceinfo.get_summary().get_nearline()),
                'GLUE2StorageServiceCapacityFreeSize':
                    as_gigabytes(spaceinfo.get_summary().get_nearline()),
                'GLUE2StorageServiceCapacityUsedSize': 0,
                'GLUE2StorageServiceCapacityReservedSize': 0
            })
            nodes.append(node)

        # GLUE2StorageAccessProtocol for each protocol
        for protocol in self._configuration.get_enabled_access_protocols():
            p_ver = self._get_access_protocol_version(protocol)
            ap_id = self._get_access_protocol_id(protocol, p_ver)
            node = GLUE2StorageAccessProtocol(ap_id, service_id)
            node.init().add({
                'GLUE2StorageAccessProtocolType': protocol,
                'GLUE2StorageAccessProtocolVersion': p_ver
                })
            nodes.append(node)

        # Glue2StorageManager
        manager_id = self._get_manager_id()
        node = GLUE2StorageManager(manager_id, service_id)
        node.init().add({
            'GLUE2ManagerProductVersion': storm_version
        })
        nodes.append(node)

        # Glue2DataStore disk online
        if spaceinfo.get_summary().has_online_capacity():
            node = GLUE2DataStore(self._get_data_store_id("disk"), manager_id, service_id)
            node.init().add({
                'GLUE2DataStoreType': "disk",
                'GLUE2DataStoreLatency': "online",
                'GLUE2DataStoreTotalSize': as_gigabytes(spaceinfo.get_summary().get_total())
            })
            nodes.append(node)

        # Glue2DataStore tape near-line
        if spaceinfo.get_summary().has_nearline_capacity():
            node = GLUE2DataStore(self._get_data_store_id("tape"), manager_id, service_id)
            node.init().add({
                'GLUE2DataStoreType': "tape",
                'GLUE2DataStoreLatency': "nearline",
                'GLUE2DataStoreTotalSize': as_gigabytes(spaceinfo.get_summary().get_nearline())
            })
            nodes.append(node)

        # Glue2Share, GLUE2MappingPolicy and Glue2StorageShareCapacity for each
        # VFS
        for name, data in spaceinfo.get_vfs().items():

            # GLUE2Share
            share_id = self._get_share_id(name)
            node = GLUE2StorageShare(share_id, service_id)
            node.init().add({
                'GLUE2StorageShareAccessLatency': data.get_accesslatency().lower(),
                'GLUE2StorageShareRetentionPolicy': data.get_retentionpolicy().lower(),
                'GLUE2StorageShareServingState': "production",
                'GLUE2StorageSharePath': data.get_stfnroot()[0]
            })
            if self._is_anonymous(data.get_voname()):
                node.add({
                    'GLUE2StorageShareSharingID': "dedicated"
                    })
            else:
                node.add({
                    'GLUE2StorageShareSharingID': self._get_sharing_id(name,
                        data.get_retentionpolicy(), data.get_accesslatency()),
                    'GLUE2StorageShareTag': data.get_voname(),
                    'GLUE2ShareDescription': "Share for " + str(data.get_voname())
                    })
            nodes.append(node)

            # GLUE2MappingPolicy
            policy_id = self._get_share_policy_id(name)
            node = GLUE2MappingPolicy(policy_id, share_id, service_id)
            node.init().add({
                'GLUE2PolicyRule': data.get_approachablerules()
            })
            if not self._is_anonymous(data.get_voname()):
                node.add({
                    'GLUE2PolicyUserDomainForeignKey': data.get_voname()
                })
            nodes.append(node)

            # Glue2StorageShareCapacities

            if data.get_space().has_online_capacity():
                # Glue2StorageShareCapacity online
                capacity_id = self._get_share_capacity_id(name, "online")
                node = GLUE2StorageShareCapacity(capacity_id, share_id, service_id)
                node.init().add({
                    'GLUE2StorageShareCapacityType': "online",
                    'GLUE2StorageShareCapacityTotalSize':
                        as_gigabytes(data.get_space().get_total()),
                    'GLUE2StorageShareCapacityFreeSize':
                        as_gigabytes(data.get_space().get_free()),
                    'GLUE2StorageShareCapacityUsedSize':
                        as_gigabytes(data.get_space().get_used()),
                    'GLUE2StorageShareCapacityReservedSize':
                        as_gigabytes(data.get_space().get_reserved())
                    })
                nodes.append(node)

            if data.get_space().has_nearline_capacity():
                # Glue2StorageShareCapacity near-line
                capacity_id = self._get_share_capacity_id(name, "nearline")
                node = GLUE2StorageShareCapacity(capacity_id, share_id, service_id)
                node.init().add({
                    'GLUE2StorageShareCapacityType': "nearline",
                    'GLUE2StorageShareCapacityTotalSize':
                        as_gigabytes(data.get_space().get_nearline()),
                    'GLUE2StorageShareCapacityFreeSize':
                        as_gigabytes(data.get_space().get_nearline()),
                    'GLUE2StorageShareCapacityUsedSize': 0,
                    'GLUE2StorageShareCapacityReservedSize': 0
                })
                nodes.append(node)

        access_policy_rules = []
        for vo in self._configuration.get_used_VOs():
            access_policy_rules.append("vo:" + vo)

        # NEW LOGIC
        if self._configuration.has_webdav():

            logging.debug("new logic webdav endpoints")
            i = 0
            for endpoint in self._configuration.get_webdav_endpoints():
                protocol = urlparse(endpoint).scheme.upper()
                if protocol == "HTTP":
                    endpoint_id = self._get_http_endpoint_id(i)
                elif protocol == "HTTPS":
                    endpoint_id = self._get_https_endpoint_id(i)
                else:
                    raise ValueError("unable to read a valid protocol from " + endpoint)
                node = GLUE2WebDAVStorageEndpoint(endpoint_id, service_id)
                node.init().add({
                    'GLUE2EndpointURL': endpoint,
                    'GLUE2EndpointImplementationVersion': storm_version,
                    'GLUE2EndpointQualityLevel': self._configuration.get_quality_level(),
                    'GLUE2EndpointServingState': self._configuration.get_serving_state(),
                    'GLUE2EndpointIssuerCA': issuer_ca
                    })
                nodes.append(node)
                # Add Endpoint Policy
                policy_id = self._get_endpoint_policy_id(endpoint_id)
                node = GLUE2AccessPolicy(policy_id, endpoint_id, service_id)
                node.init().add({
                    'GLUE2PolicyRule': access_policy_rules,
                    'GLUE2PolicyUserDomainForeignKey': self._configuration.get_used_VOs()
                    })
                nodes.append(node)
                i += 1

        else:

            # OLD_LOGIC
            if self._configuration.has_gridhttps():

                # Add HTTP WebDAV Endpoint
                endpoint_id = self._get_http_endpoint_id()
                node = GLUE2WebDAVStorageEndpoint(endpoint_id, service_id)
                node.init().add({
                    'GLUE2EndpointURL': self._configuration.get_public_http_endpoint(),
                    'GLUE2EndpointImplementationVersion': storm_version,
                    'GLUE2EndpointQualityLevel': self._configuration.get_quality_level(),
                    'GLUE2EndpointServingState': self._configuration.get_serving_state(),
                    'GLUE2EndpointIssuerCA': issuer_ca
                    })
                nodes.append(node)

                # Add Endpoint Policy
                policy_id = self._get_endpoint_policy_id(endpoint_id)
                node = GLUE2AccessPolicy(policy_id, endpoint_id, service_id)
                node.init().add({
                    'GLUE2PolicyRule': access_policy_rules,
                    'GLUE2PolicyUserDomainForeignKey': self._configuration.get_used_VOs()
                    })
                nodes.append(node)

                # Add HTTPs Endpoint
                endpoint_id = self._get_https_endpoint_id()
                node = GLUE2WebDAVStorageEndpoint(endpoint_id, service_id)
                node.init().add({
                    'GLUE2EndpointURL': self._configuration.get_public_https_endpoint(),
                    'GLUE2EndpointImplementationVersion': storm_version,
                    'GLUE2EndpointQualityLevel': self._configuration.get_quality_level(),
                    'GLUE2EndpointServingState': self._configuration.get_serving_state(),
                    'GLUE2EndpointIssuerCA': issuer_ca
                    })
                nodes.append(node)

                # Add Endpoint Policy
                policy_id = self._get_endpoint_policy_id(endpoint_id)
                node = GLUE2AccessPolicy(policy_id, endpoint_id, service_id)
                node.init().add({
                    'GLUE2PolicyRule': access_policy_rules,
                    'GLUE2PolicyUserDomainForeignKey': self._configuration.get_used_VOs()
                    })
                nodes.append(node)

        return nodes

    def get_update_ldif_endpoints(self, serving_state_value):

        # Output
        nodes = []

        # Commons
        service_ID = self._get_service_id()

        # Glue2StorageEndpoint SRM serving_state_value
        node = GLUE2StorageEndpoint(self._get_srm_endpoint_id(), service_ID)
        node.add({ 'GLUE2EndpointServingState': serving_state_value })
        nodes.append(node)

        if self._configuration.has_webdav():

            i = 0
            for endpoint in self._configuration.get_webdav_endpoints():
                protocol = urlparse(endpoint).scheme.upper()
                if protocol == "HTTP":
                    endpoint_id = self._get_http_endpoint_id(i)
                elif protocol == "HTTPS":
                    endpoint_id = self._get_https_endpoint_id(i)
                else:
                    raise ValueError("unable to read a valid protocol from " + endpoint)
                # Glue2StorageEndpoint http webdav serving_state_value
                node = GLUE2StorageEndpoint(endpoint_id, service_ID)
                node.add({ 'GLUE2EndpointServingState': serving_state_value })
                nodes.append(node)
                i += 1

        elif self._configuration.has_gridhttps():

            # Glue2StorageEndpoint http webdav serving_state_value
            node = GLUE2StorageEndpoint(self._get_http_endpoint_id(),
                service_ID)
            node.add({ 'GLUE2EndpointServingState': serving_state_value })
            nodes.append(node)

            # Glue2StorageEndpoint https webdav serving_state_value
            node = GLUE2StorageEndpoint(self._get_https_endpoint_id(),
                service_ID)
            node.add({ 'GLUE2EndpointServingState': serving_state_value })
            nodes.append(node)

        return nodes

    def get_update_ldif_spaceinfo(self, spaceinfo, serving_state_value):

        # Output
        nodes = []

        # Commons
        service_ID = self._get_service_id()

        # Glue2StorageServiceCapacity online
        if spaceinfo.get_summary().has_online_capacity():
            sc_id = self._get_service_capacity_id("online")
            node = GLUE2StorageServiceCapacity(sc_id, service_ID)
            node.add({
                'GLUE2StorageServiceCapacityTotalSize':
                    as_gigabytes(spaceinfo.get_summary().get_total()),
                'GLUE2StorageServiceCapacityFreeSize':
                    as_gigabytes(spaceinfo.get_summary().get_free()),
                'GLUE2StorageServiceCapacityUsedSize':
                    as_gigabytes(spaceinfo.get_summary().get_used()),
                'GLUE2StorageServiceCapacityReservedSize':
                    as_gigabytes(spaceinfo.get_summary().get_reserved())
            })
            nodes.append(node)

        # Glue2StorageServiceCapacity near-line
        if spaceinfo.get_summary().has_nearline_capacity():
            sc_id = self._get_service_capacity_id("nearline")
            node = GLUE2StorageServiceCapacity(sc_id, service_ID)
            node.add({
                'GLUE2StorageServiceCapacityTotalSize':
                    as_gigabytes(spaceinfo.get_summary().get_nearline()),
                'GLUE2StorageServiceCapacityFreeSize':
                    as_gigabytes(spaceinfo.get_summary().get_nearline()),
                'GLUE2StorageServiceCapacityUsedSize': 0,
                'GLUE2StorageServiceCapacityReservedSize': 0
            })
            nodes.append(node)

        # Glue2Share, GLUE2MappingPolicy and Glue2StorageShareCapacity for each
        # VFS
        for name, data in spaceinfo.get_vfs().iteritems():

            # GLUE2Share
            share_id = self._get_share_id(name)
            node = GLUE2StorageShare(share_id, service_ID)
            node.add({ 'GLUE2StorageShareServingState': serving_state_value })
            nodes.append(node)

            # Glue2StorageShareCapacity
            if data.get_space().has_online_capacity():
                capacity_id = self._get_share_capacity_id(name, "online")
                node = GLUE2StorageShareCapacity(capacity_id, share_id, service_ID)
                node.add({
                    'GLUE2StorageShareCapacityTotalSize':
                        as_gigabytes(data.get_space().get_total()),
                    'GLUE2StorageShareCapacityFreeSize':
                        as_gigabytes(data.get_space().get_free()),
                    'GLUE2StorageShareCapacityUsedSize':
                        as_gigabytes(data.get_space().get_used()),
                    'GLUE2StorageShareCapacityReservedSize':
                        as_gigabytes(data.get_space().get_reserved())
                })
                nodes.append(node)
            if data.get_space().has_nearline_capacity():
                capacity_id = self._get_share_capacity_id(name, "nearline")
                node = GLUE2StorageShareCapacity(capacity_id, share_id, service_ID)
                node.add({
                    'GLUE2StorageShareCapacityTotalSize':
                        as_gigabytes(data.get_space().get_nearline()),
                    'GLUE2StorageShareCapacityFreeSize':
                        as_gigabytes(data.get_space().get_nearline()),
                    'GLUE2StorageShareCapacityUsedSize': 0,
                    'GLUE2StorageShareCapacityReservedSize': 0
                })
                nodes.append(node)

        return nodes

    def _delete_backup_files(self):
        parent_directory = os.path.dirname(GLUE2_INFO_STATIC_LDIF_FILE)
        removed_list = []
        for f in os.listdir(parent_directory):
            if re.search(r'storm-glue2-static\.ldif\.bkp_.*', f):
                os.remove(os.path.join(parent_directory, f))
                removed_list.append(f)
        logging.debug("Removed backup files: [%s]", removed_list)
        return len(removed_list)
