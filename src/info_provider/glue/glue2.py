import logging
import os
import re
import time

from info_provider.glue.constants import *
from info_provider.ldap_utils import LDIFExporter
from glue2_schema import *
from utils import *

class QualityLevel_t:
    _quality_levels = ["development", "pre-production", "production", "testing"]
    def __init__(self, int_value):
        self._int_value = int(int_value)
        return
    def __str__(self):
        return self._quality_levels[self._int_value]

class Glue2(object):
    
    def __init__(self, configuration, spaceinfo):
        self._configuration = configuration
        self._stats = spaceinfo
        return

    def _get_access_protocol_version(self, name):
        return GLUE2_ACCESS_PROTOCOLS_VERSIONS[name]

    def _get_service_id(self):
        return self._configuration.get("STORM_BACKEND_HOST") + "/storage"

    def _get_site_id(self):
        return self._configuration.get("SITE_NAME")

    def _get_manager_id(self):
        return self._get_service_id() + "/manager"

    def _get_srm_endpoint_id(self):
        return self._get_service_id() + "/endpoint/SRM"

    def _get_http_endpoint_id(self):
        return self._get_service_id() + "/endpoint/HTTP"

    def _get_https_endpoint_id(self):
        return self._get_service_id() + "/endpoint/HTTPS"

    def _get_endpoint_policy_id(self, endpoint_id):
        return endpoint_id + "_Policy"

    def _get_service_capacity_id(self, capacity_type):
        return self._get_service_id() + "/capacity/" + capacity_type

    def _get_access_protocol_id(self, name, version):
        return self._get_service_id() + "/accessprotocol/" + name + "/" + version

    def _get_data_store_id(self, ds_type):
        return self._get_service_id()  + "/datastore/" + ds_type

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

    def _get_quality_level(self):
        int_value = int(self._configuration.get('STORM_ENDPOINT_QUALITY_LEVEL'))
        return str(QualityLevel_t(int_value))

    def _get_implementation_version(self):
        cmd = "rpm -q --queryformat='%{VERSION}' storm-backend-server"
        return os.popen(cmd).read()

    def _has_online_capacity(self):
        return int(self._stats.get_summary()["total-space"]) > 0

    def _has_nearline_capacity(self):
        return int(self._stats.get_summary()["nearline-space"]) > 0

    def _share_has_online_capacity(self, vfs_name):
        return int(self._stats.get_vfs()[vfs_name]["total-space"]) > 0

    def _share_has_nearline_capacity(self, vfs_name):
        return int(self._stats.get_vfs()[vfs_name]["nearline-space"]) > 0

    def configure(self):
        # remove old static ldif backup files
        self._delete_backup_files()
        # create Glue2 service configuration file
        logging.debug("Creating %s ...", GLUE2_INFO_SERVICE_CONFIG_FILE)
        self._create_service_config_file()
        logging.info("Successfully created %s !", 
            GLUE2_INFO_SERVICE_CONFIG_FILE)
        # create Glue2 srm endpoint configuration file
        logging.debug("Creating %s ...", GLUE2_INFO_SERVICE_SRM_CONFIG_FILE)
        self._create_srm_endpoint_config_file()
        logging.info("Successfully created %s !", 
            GLUE2_INFO_SERVICE_SRM_CONFIG_FILE)
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
        self._create_static_ldif_file()
        logging.info("Successfully created %s !", GLUE2_INFO_STATIC_LDIF_FILE)
        return

    def _create_service_config_file(self):
        params = { 
            'SITEID': self._get_site_id(),
            'SERVICEID': self._get_service_id(),
            'QUALITY_LEVEL': self._get_quality_level()
        }
        create_file_from_template(
            GLUE2_INFO_SERVICE_CONFIG_FILE,
            GLUE2_INFO_SERVICE_CONFIG_FILE_TEMPLATE,
            params)
        #set_owner("ldap", GLUE2_INFO_SERVICE_CONFIG_FILE)
        return

    def _create_srm_endpoint_config_file(self):
        vos = self._configuration.get_supported_VOs()
        params = {
            'SITEID': self._get_site_id(),
            'ENDPOINT': self._configuration.get_public_srm_endpoint(),
            'QUALITY_LEVEL': self._get_quality_level(),
            'SERVICEID': self._get_service_id(),
            'ACBR': "VO:" + "\\nVO:".join(vos),
            'OWNER': "\\n".join(vos)
        }
        create_file_from_template(
            GLUE2_INFO_SERVICE_SRM_CONFIG_FILE, 
            GLUE2_INFO_SERVICE_SRM_CONFIG_FILE_TEMPLATE, 
            params)
        # set owner
        #set_owner("ldap", GLUE2_INFO_SERVICE_SRM_CONFIG_FILE)
        return

    def _create_service_provider_file(self):
        # create (overwrite) provider file
        f = open(GLUE2_INFO_PROVIDER_FILE, "w")
        f.write("#!/bin/sh\n")
        f.write("glite-info-glue2-simple ")
        f.write("%s,%s " % (GLUE2_INFO_SERVICE_SRM_CONFIG_FILE, 
            GLUE2_INFO_SERVICE_CONFIG_FILE))
        f.write("%s " % (self._get_site_id()))
        f.write("%s " % (self._get_service_id()))
        f.write("%s\n" % (self._get_srm_endpoint_id()))
        f.close()
        # set ldap as owner and chmod +x
        set_owner("ldap",GLUE2_INFO_PROVIDER_FILE)
        os.chmod(GLUE2_INFO_PROVIDER_FILE, 0755)
        return

    def _create_plugin_file(self):
        f = open(GLUE2_INFO_PLUGIN_FILE, "w")
        f.write("#!/bin/sh\n")
        f.write("%s -o %s get-update-ldif -f %s -g glue2" % (
            STORM_INFO_PROVIDER, LOG_FILE, CONFIG_FILE))
        f.close()
        # set ldap as owner and chmod +x
        set_owner("ldap",GLUE2_INFO_PLUGIN_FILE)
        os.chmod(GLUE2_INFO_PLUGIN_FILE, 0755)
        return

    def _create_static_ldif_file(self):
        exporter = LDIFExporter()
        exporter.add_nodes(self.get_static_ldif_nodes())
        exporter.save_to_file(GLUE2_INFO_STATIC_LDIF_FILE)
        # set ldap as owner and chmod +x
        set_owner("ldap", GLUE2_INFO_STATIC_LDIF_FILE)
        return

    def get_static_ldif_nodes(self):

        nodes = []
        # Commons
        service_id = self._get_service_id()
        storm_version = self._get_implementation_version()
        issuer_ca = str(os.popen("openssl x509 -issuer -noout -in \
            /etc/grid-security/hostcert.pem").read())[8:-1]
        
        # Glue2StorageService
        # NOTE: It must be removed when 'storm' type will be added
        node = GLUE2StorageService(service_id)
        node.init().add({
            'GLUE2ServiceQualityLevel': self._get_quality_level(),
            'GLUE2ServiceAdminDomainForeignKey': self._get_site_id()
            })
        nodes.append(node)

        # Glue2StorageServiceCapacity online
        if self._has_online_capacity():
            node = GLUE2StorageServiceCapacity(
                self._get_service_capacity_id("online"), service_id)
            node.init().add({
                'GLUE2StorageServiceCapacityType': "online",
                'GLUE2StorageServiceCapacityTotalSize': 
                    self._stats.get_summary()["total-space"].as_GB(), 
                'GLUE2StorageServiceCapacityFreeSize': 
                    self._stats.get_summary()["free-space"].as_GB(), 
                'GLUE2StorageServiceCapacityUsedSize': 
                    self._stats.get_summary()["used-space"].as_GB(), 
                'GLUE2StorageServiceCapacityReservedSize': 
                    self._stats.get_summary()["reserved-space"].as_GB(),
            })
            nodes.append(node)

        # Glue2StorageServiceCapacity nearline
        if self._has_nearline_capacity():
            node = GLUE2StorageServiceCapacity(
                self._get_service_capacity_id("nearline"), service_id)
            node.init().add({
                'GLUE2StorageServiceCapacityType': "nearline",
                'GLUE2StorageServiceCapacityTotalSize': 
                    self._stats.get_summary()["nearline-space"].as_GB(), 
                'GLUE2StorageServiceCapacityFreeSize': 
                    self._stats.get_summary()["nearline-space"].as_GB(), 
                'GLUE2StorageServiceCapacityUsedSize': 0, 
                'GLUE2StorageServiceCapacityReservedSize': 0,
            })
            nodes.append(node)

        # GLUE2StorageAccessProtocol for each protocol
        for protocol in self._configuration.get_enabled_access_protocols():
            ap_id = self._get_access_protocol_id(protocol, 
                self._get_access_protocol_version(protocol))
            node = GLUE2StorageAccessProtocol(ap_id, service_id)
            node.init().add({
                'GLUE2StorageAccessProtocolType': protocol, 
                'GLUE2StorageAccessProtocolVersion': 
                    self._get_access_protocol_version(protocol)
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
        if self._has_online_capacity():
            node = GLUE2DataStore(self._get_data_store_id("disk"), manager_id, 
                service_id)
            node.init().add({
                'GLUE2DataStoreType': "disk", 
                'GLUE2DataStoreLatency': "online", 
                'GLUE2DataStoreTotalSize': 
                    self._stats.get_summary()["total-space"].as_GB()
            })
            nodes.append(node)

        # Glue2DataStore tape nearline
        if self._has_nearline_capacity():
            node = GLUE2DataStore(self._get_data_store_id("tape"), manager_id, 
                service_id)
            node.init().add({
                'GLUE2DataStoreType': "tape", 
                'GLUE2DataStoreLatency': "nearline", 
                'GLUE2DataStoreTotalSize': 
                    self._stats.get_summary()["nearline-space"].as_GB()
            })
            nodes.append(node)

        # Glue2Share, GLUE2MappingPolicy and Glue2StorageShareCapacity for each 
        # VFS
        for sa_name,sa_data in self._stats.get_vfs().items():

            # GLUE2Share
            share_id = self._get_share_id(sa_data["name"])
            if self._is_anonymous(sa_data["voname"]):
                sharing_id = "dedicated"
            else:
                sharing_id = self._get_sharing_id(sa_data["name"],
                    sa_data["retentionPolicy"],sa_data["accessLatency"])
            node = GLUE2StorageShare(share_id, service_id)
            node.init().add({
                'GLUE2StorageShareAccessLatency': 
                    sa_data["accessLatency"].lower(),
                'GLUE2StorageShareRetentionPolicy': 
                    sa_data["retentionPolicy"].lower(),
                'GLUE2StorageShareServingState': "production",
                'GLUE2StorageShareSharingID': sharing_id
            })
            nodes.append(node)

            # GLUE2MappingPolicy
            policy_id = self._get_share_policy_id(sa_data["name"])
            node = GLUE2MappingPolicy(policy_id, share_id, service_id)
            node.init().add({
                'GLUE2PolicyRule': sa_data["approachableRules"]
            })
            if not self._is_anonymous(sa_data["voname"]):
                node.add({ 
                    'GLUE2PolicyUserDomainForeignKey': sa_data["voname"] 
                })
            nodes.append(node)
            
            # Glue2StorageShareCapacities

            if self._share_has_online_capacity(sa_name): 
                # Glue2StorageShareCapacity online

                capacity_id = self._get_share_capacity_id(sa_data["name"], 
                    "online")
                node = GLUE2StorageShareCapacity(capacity_id, share_id, 
                    service_id)
                node.init().add({
                    'GLUE2StorageShareCapacityType': "online",
                    'GLUE2StorageShareCapacityTotalSize': 
                        sa_data["total-space"].as_GB(), 
                    'GLUE2StorageShareCapacityFreeSize': 
                        sa_data["free-space"].as_GB(), 
                    'GLUE2StorageShareCapacityUsedSize': 
                        sa_data["used-space"].as_GB(), 
                    'GLUE2StorageShareCapacityReservedSize': 
                        sa_data["reserved-space"].as_GB()
                })
                nodes.append(node)

            if self._share_has_nearline_capacity(sa_name): 
                # Glue2StorageShareCapacity nearline
                capacity_id = self._get_share_capacity_id(sa_data["name"], 
                    "nearline")
                node = GLUE2StorageShareCapacity(capacity_id, share_id, 
                    service_id)
                node.init().add({
                    'GLUE2StorageShareCapacityType': "nearline",
                    'GLUE2StorageShareCapacityTotalSize': 
                        sa_data["nearline-space"].as_GB(), 
                    'GLUE2StorageShareCapacityFreeSize': 
                        sa_data["nearline-space"].as_GB(), 
                    'GLUE2StorageShareCapacityUsedSize': 0, 
                    'GLUE2StorageShareCapacityReservedSize': 0
                })
                nodes.append(node)

        access_policy_rules = []
        for vo in self._configuration.get_supported_VOs():
            access_policy_rules.append("vo:" + vo)

        if self._configuration.has_gridhttps():

            # Add HTTP Endpoint
            endpoint_id = self._get_http_endpoint_id()
            node = GLUE2HttpStorageEndpoint(endpoint_id, service_id)
            node.init().add({
                'GLUE2EndpointURL': 
                    self._configuration.get_public_http_endpoint(),
                'GLUE2EndpointImplementationVersion': storm_version,
                'GLUE2EndpointQualityLevel': self._get_quality_level(),
                'GLUE2EndpointServingState': 
                    self._configuration.get("STORM_SERVING_STATE"),
                'GLUE2EndpointIssuerCA': issuer_ca
            })
            nodes.append(node)

            # Add Endpoint Policy
            policy_id = self._get_endpoint_policy_id(endpoint_id)
            node = GLUE2AccessPolicy(policy_id, endpoint_id, service_id)
            node.init().add({ 
                'GLUE2PolicyRule': access_policy_rules,
                'GLUE2PolicyUserDomainForeignKey': 
                    self._configuration.get_supported_VOs()
                })
            nodes.append(node)

            # Add HTTPs Endpoint
            endpoint_id = self._get_https_endpoint_id()
            node = GLUE2HttpsStorageEndpoint(endpoint_id, service_id)
            node.init().add({
                'GLUE2EndpointURL': 
                    self._configuration.get_public_https_endpoint(),
                'GLUE2EndpointImplementationVersion': storm_version,
                'GLUE2EndpointQualityLevel': self._get_quality_level(),
                'GLUE2EndpointServingState': 
                    self._configuration.get("STORM_SERVING_STATE"),
                'GLUE2EndpointIssuerCA': issuer_ca
            })
            nodes.append(node)

            # Add Endpoint Policy
            policy_id = self._get_endpoint_policy_id(endpoint_id)
            node = GLUE2AccessPolicy(policy_id, endpoint_id, service_id)
            node.init().add({ 
                'GLUE2PolicyRule': access_policy_rules,
                'GLUE2PolicyUserDomainForeignKey': 
                    self._configuration.get_supported_VOs()
                })
            nodes.append(node)

        return nodes

    def get_update_ldif_nodes(self):

        # Output
        nodes = []

        # Commons
        service_ID = self._get_service_id()
        serving_state_value = self._configuration.get("STORM_SERVING_STATE")

        # Glue2StorageEndpoint SRM
        node = GLUE2StorageEndpoint(self._get_srm_endpoint_id(), service_ID)
        node.add({ 'GLUE2EndpointServingState': serving_state_value })
        nodes.append(node)

        if self._configuration.has_gridhttps():

            # Glue2StorageEndpoint http webdav
            node = GLUE2StorageEndpoint(self._get_http_endpoint_id(), 
                service_ID)
            node.add({ 'GLUE2EndpointServingState': serving_state_value })
            nodes.append(node)

            # Glue2StorageEndpoint https webdav
            node = GLUE2StorageEndpoint(self._get_https_endpoint_id(), 
                service_ID)
            node.add({ 'GLUE2EndpointServingState': serving_state_value })
            nodes.append(node)

        # Glue2StorageServiceCapacity online
        if self._has_online_capacity():
            node = GLUE2StorageServiceCapacity(
                self._get_service_capacity_id("online"), service_ID)
            node.add({ 
                'GLUE2StorageServiceCapacityTotalSize': 
                    self._stats.get_summary()["total-space"].as_GB(), 
                'GLUE2StorageServiceCapacityFreeSize': 
                    self._stats.get_summary()["free-space"].as_GB(), 
                'GLUE2StorageServiceCapacityUsedSize': 
                    self._stats.get_summary()["used-space"].as_GB(), 
                'GLUE2StorageServiceCapacityReservedSize': 
                    self._stats.get_summary()["reserved-space"].as_GB()
            })
            nodes.append(node)

        # Glue2StorageServiceCapacity nearline
        if self._has_nearline_capacity():
            node = GLUE2StorageServiceCapacity(
                self._get_service_capacity_id("nearline"), service_ID)
            node.add({ 
                'GLUE2StorageServiceCapacityTotalSize': 
                    self._stats.get_summary()["nearline-space"].as_GB(), 
                'GLUE2StorageServiceCapacityFreeSize': 
                    self._stats.get_summary()["nearline-space"].as_GB(),
                'GLUE2StorageServiceCapacityUsedSize': 0, 
                'GLUE2StorageServiceCapacityReservedSize': 0
            })
            nodes.append(node)

        # Glue2Share, GLUE2MappingPolicy and Glue2StorageShareCapacity for each 
        # VFS
        for sa_name,sa_data in self._stats.get_vfs().items():

            # GLUE2Share
            share_id = self._get_share_id(sa_data["name"])
            node = GLUE2StorageShare(share_id, service_ID)
            node.add({ 'GLUE2StorageShareServingState': serving_state_value })
            nodes.append(node)
            
            # Glue2StorageShareCapacity
            if self._share_has_online_capacity(sa_name):
                capacity_id = self._get_share_capacity_id(sa_data["name"], 
                    "online")
                node = GLUE2StorageShareCapacity(capacity_id, share_id, 
                    service_ID)
                node.add({ 
                    'GLUE2StorageShareCapacityTotalSize': 
                        sa_data["total-space"].as_GB(), 
                    'GLUE2StorageShareCapacityFreeSize': 
                        sa_data["free-space"].as_GB(), 
                    'GLUE2StorageShareCapacityUsedSize': 
                        sa_data["used-space"].as_GB(), 
                    'GLUE2StorageShareCapacityReservedSize': 
                        sa_data["reserved-space"].as_GB()
                })
                nodes.append(node)
            if self._share_has_nearline_capacity(sa_name):
                capacity_id = self._get_share_capacity_id(sa_data["name"], 
                    "nearline")
                node = GLUE2StorageShareCapacity(capacity_id, share_id, 
                    service_ID)
                node.add({ 
                    'GLUE2StorageShareCapacityTotalSize': 
                        sa_data["nearline-space"].as_GB(), 
                    'GLUE2StorageShareCapacityFreeSize': 
                        sa_data["nearline-space"].as_GB(), 
                    'GLUE2StorageShareCapacityUsedSize': 0, 
                    'GLUE2StorageShareCapacityReservedSize': 0
                })
                nodes.append(node)

        return nodes

    def _delete_backup_files(self):
        parent_directory = os.path.dirname(GLUE2_INFO_STATIC_LDIF_FILE)
        removed_list = []
        for f in os.listdir(parent_directory):
            if re.search(r'storm-glue2-static\.ldif\.bkp_.*',f):
                os.remove(os.path.join(parent_directory, f))
                removed_list.append(f)
        logging.debug("Removed backup files: [%s]", removed_list)
        return len(removed_list)        

