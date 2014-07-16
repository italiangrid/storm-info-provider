import logging
import os
import re

from configuration import Configuration
from glue import *
from glue2data import *
from utils import round_div,delete_files

class Glue2(Glue):

    FROM_BYTES_TO_GB = 1000000000
    FROM_BYTES_TO_KB = 1000

    GLUE2_INFO_SERVICE = GlueConstants.INFO_SERVICE_SCRIPT + "/glite-info-glue2-simple"
    GLUE2_SERVICE_FILE = GlueConstants.INFO_PROVIDER_PATH + "/service-glue2-srm-storm-v2"
    GLUE2_SERVICE_CONFIG_FILE = GlueConstants.INFO_SERVICE_CONFIG + "/glite-info-service-glue2-srm-storm-v2.conf"
    GLUE2_STATIC_LDIF_FILE = GlueConstants.INFO_LDIF_PATH + "/static-file-glue2-storm.ldif"
    GLUE2_INFO_PLUGIN_FILE = GlueConstants.INFO_PLUGIN_PATH + "/glite-info-glue2-dynamic-storm"

    def __init__(self):
        self.access_protocols_versions = { 
            'file': '1.0.0', 
            'rfio': '1.0.0', 
            'gsiftp': '2.0.0', 
            'root': '1.0.0', 
            'http': '1.1.0', 
            'https': '1.1.0' 
        }
        return

    def init(self, configuration, stats):
        # GLUE2_SERVICE_FILE
        logging.debug("Creating %s ...", self.GLUE2_SERVICE_FILE)
        self.create_service_file(configuration)
        logging.info("Successfully created %s !", self.GLUE2_SERVICE_FILE)
        # GLUE2_SERVICE_CONFIG_FILE
        logging.debug("Creating %s ...", self.GLUE2_SERVICE_CONFIG_FILE)
        self.create_service_config_file(configuration, stats)
        logging.info("Successfully created %s !", self.GLUE2_SERVICE_CONFIG_FILE)
        # GLUE2_STATIC_LDIF_FILE
        logging.debug("Creating %s ...", self.GLUE2_STATIC_LDIF_FILE)
        created_file = self.create_static_ldif_file(configuration, stats)
        logging.info("Successfully created %s !", created_file)
        # GLUE2_PLUGIN_FILE
        logging.debug("Creating %s ...", self.GLUE2_INFO_PLUGIN_FILE)
        self.create_plugin_file()
        logging.info("Successfully created %s !", self.GLUE2_INFO_PLUGIN_FILE)
        # remove old cron file
        self.remove_old_cron_file_if_exists()
        return

    def update(self, configuration, stats):
        # change service configuration file
        content = self.get_service_configuration(configuration, stats.get_managed_vos())
        content['get_servingstate'] = "echo " + str(configuration.get("STORM_SERVING_STATE"))
        super(Glue2, self).create_service_config_file(self.GLUE2_SERVICE_CONFIG_FILE, content)
        # generates the updater node list
        node_list = self.get_update_nodes(configuration, stats)
        # print LDIF
        return super(Glue2, self).print_update_ldif(node_list)

    def create_service_file(self, configuration):
        params = []
        params.append(configuration.get('SITE_NAME'))
        params.append(configuration.get_public_srm_endpoint())
        return super(Glue2, self).create_service_file(self.GLUE2_SERVICE_FILE, self.GLUE2_INFO_SERVICE, self.GLUE2_SERVICE_CONFIG_FILE, params)

    def create_service_config_file(self, configuration, stats):
        content = self.get_service_configuration(configuration, stats.get_managed_vos())
        return super(Glue2, self).create_service_config_file(self.GLUE2_SERVICE_CONFIG_FILE, content)

    def create_plugin_file(self):
        params = ["/etc/storm/backend-server/storm-yaim-variables.conf"]
        info_service = "/usr/libexec/storm-dynamic-info-provider/glite-info-glue2-dynamic-storm"
        return super(Glue2, self).create_plugin_file(self.GLUE2_INFO_PLUGIN_FILE, info_service, params)

    def create_static_ldif_file(self, configuration, stats):

        nodes = []
        # Commons
        GLUE2ServiceID = "glue:" + configuration.get("STORM_FRONTEND_PUBLIC_HOST") + "/data"
        GLUE2EntityCreationTime = time.strftime('%Y-%m-%dT%T')
        GLUE2ServiceQualityLevel = str(QualityLevel_t(int(configuration.get('STORM_ENDPOINT_QUALITY_LEVEL'))))

        # Glue2StorageService
        node = GLUE2StorageService(GLUE2ServiceID)
        node.init_as_default().add({
            'GLUE2ServiceID': [GLUE2ServiceID],
            'GLUE2EntityCreationTime': [GLUE2EntityCreationTime],
            'GLUE2ServiceQualityLevel': [GLUE2ServiceQualityLevel],
            'GLUE2ServiceAdminDomainForeignKey': [configuration.get("SITE_NAME")]
        })
        nodes.append(node)

        # Glue2StorageServiceCapacity online
        if stats.get_summary()["total-space"] > 0:
            GLUE2StorageServiceCapacityID = GLUE2ServiceID + "/ssc/disk"
            node = GLUE2StorageServiceCapacity(GLUE2StorageServiceCapacityID, GLUE2ServiceID)
            node.init_as_default().add({
                'GLUE2StorageServiceCapacityID': [GLUE2StorageServiceCapacityID],
                'GLUE2EntityCreationTime': [GLUE2EntityCreationTime],
                'GLUE2StorageServiceCapacityType': ["online"],
                'GLUE2StorageServiceCapacityTotalSize': [str(round_div(stats.get_summary()["total-space"],self.FROM_BYTES_TO_GB))], 
                'GLUE2StorageServiceCapacityFreeSize': [str(round_div(stats.get_summary()["free-space"],self.FROM_BYTES_TO_GB))], 
                'GLUE2StorageServiceCapacityUsedSize': [str(round_div(stats.get_summary()["used-space"],self.FROM_BYTES_TO_GB))], 
                'GLUE2StorageServiceCapacityReservedSize': [str(round_div(stats.get_summary()["reserved-space"],self.FROM_BYTES_TO_GB))],
                'GLUE2StorageServiceCapacityStorageServiceForeignKey': [GLUE2ServiceID]
            })
            nodes.append(node)

        # Glue2StorageServiceCapacity nearline
        if stats.get_summary()["nearline-space"] > 0:
            GLUE2StorageServiceCapacityID = GLUE2ServiceID + "/ssc/tape"
            node = GLUE2StorageServiceCapacity(GLUE2StorageServiceCapacityID, GLUE2ServiceID)
            node.init_as_default().add({
                'GLUE2StorageServiceCapacityID': [GLUE2StorageServiceCapacityID],
                'GLUE2EntityCreationTime': [GLUE2EntityCreationTime],
                'GLUE2StorageServiceCapacityType': ["nearline"],
                'GLUE2StorageServiceCapacityTotalSize': [str(round_div(stats.get_summary()["nearline-space"],self.FROM_BYTES_TO_GB))], 
                'GLUE2StorageServiceCapacityFreeSize': [str(round_div(stats.get_summary()["nearline-space"],self.FROM_BYTES_TO_GB))], 
                'GLUE2StorageServiceCapacityUsedSize': [str(0)], 
                'GLUE2StorageServiceCapacityReservedSize': [str(0)],
                'GLUE2StorageServiceCapacityStorageServiceForeignKey': [GLUE2ServiceID]
            })
            nodes.append(node)

        # GLUE2StorageAccessProtocol for each protocol
        protocol_versions = self.get_enabled_protocols(configuration)
        for protocol in protocol_versions:
            GLUE2StorageAccessProtocolID = GLUE2ServiceID + "/ap/" + protocol + "/" + protocol_versions[protocol]
            node = GLUE2StorageAccessProtocol(GLUE2StorageAccessProtocolID, GLUE2ServiceID).init_as_default()
            node.add({
                'GLUE2StorageAccessProtocolID': [GLUE2StorageAccessProtocolID],
                'GLUE2EntityCreationTime': [GLUE2EntityCreationTime],
                'GLUE2StorageAccessProtocolType': [protocol], 
                'GLUE2StorageAccessProtocolVersion': [protocol_versions[protocol]],
                'GLUE2StorageAccessProtocolStorageServiceForeignKey': [GLUE2ServiceID],
                'GLUE2ManagerServiceForeignKey': [GLUE2ServiceID] # it seems necessary
            })
            nodes.append(node)

        # Glue2StorageManager
        GLUE2ManagerID = GLUE2ServiceID + "/m/StoRM"
        node = GLUE2StorageManager(GLUE2ManagerID, GLUE2ServiceID)
        node.init_as_default().add({
            'GLUE2ManagerID': [GLUE2ManagerID],
            'GLUE2EntityCreationTime': [GLUE2EntityCreationTime],
            'GLUE2StorageManagerStorageServiceForeignKey': [GLUE2ServiceID]
        })
        nodes.append(node)

        # Glue2DataStore
        if stats.get_summary()["total-space"] > 0:
            # Glue2DataStore disk online
            GLUE2ResourceID = GLUE2ServiceID + "/ds/StoRM/disk"
            node = GLUE2DataStore(GLUE2ResourceID, GLUE2ManagerID, GLUE2ServiceID)
            node.init_as_default().add({
                'GLUE2ResourceID': [GLUE2ResourceID],
                'GLUE2EntityCreationTime': [GLUE2EntityCreationTime],
                'GLUE2DataStoreType': ["disk"], 
                'GLUE2DataStoreLatency': ["online"], 
                'GLUE2DataStoreTotalSize': [str(round_div(stats.get_summary()["total-space"],self.FROM_BYTES_TO_GB))],
                'GLUE2ResourceManagerForeignKey': [GLUE2ManagerID],
                'GLUE2DataStoreStorageManagerForeignKey': [GLUE2ManagerID] # it seems necessary
            })
            nodes.append(node)

        if stats.get_summary()["nearline-space"] > 0:
            # Glue2DataStore tape nearline
            GLUE2ResourceID = GLUE2ServiceID + "/ds/StoRM/tape"
            node = GLUE2DataStore(GLUE2ResourceID, GLUE2ManagerID, GLUE2ServiceID)
            node.init_as_default().add({
                'GLUE2ResourceID': [GLUE2ResourceID],
                'GLUE2EntityCreationTime': [GLUE2EntityCreationTime],
                'GLUE2DataStoreType': ["tape"], 
                'GLUE2DataStoreLatency': ["nearline"], 
                'GLUE2DataStoreTotalSize': [str(round_div(stats.get_summary()["nearline-space"],self.FROM_BYTES_TO_GB))], 
                'GLUE2ResourceManagerForeignKey': [GLUE2ManagerID],
                'GLUE2DataStoreStorageManagerForeignKey': [GLUE2ManagerID] # it seems necessary
            })
            nodes.append(node)

        # Glue2Share, GLUE2MappingPolicy and Glue2StorageShareCapacity for each VFS
        for sa_name,sa_data in stats.get_vfs().items():

            # GLUE2Share
            GLUE2ShareID = GLUE2ServiceID + "/ss/" + sa_data["name"]
            node = GLUE2StorageShare(GLUE2ShareID, GLUE2ServiceID)
            node.init_as_default().add({
                'GLUE2ShareID': [GLUE2ShareID],
                'GLUE2EntityCreationTime': [GLUE2EntityCreationTime],
                'GLUE2StorageShareAccessLatency': [sa_data["accessLatency"].lower()],
                'GLUE2StorageShareRetentionPolicy': [sa_data["retentionPolicy"].lower()],
                'GLUE2StorageShareServingState': ["production"],
                'GLUE2StorageShareStorageServiceForeignKey': [GLUE2ServiceID],
                'GLUE2ShareServiceForeignKey': [GLUE2ServiceID] # it seems necessary
            })
            if "*" in sa_data["voname"]:
                node.add({'GLUE2StorageShareSharingID': ["dedicated"]})
            else:
                s_id = ":".join((sa_data["voname"],sa_data["retentionPolicy"],sa_data["accessLatency"]))
                node.add({'GLUE2StorageShareSharingID': [s_id]})
            nodes.append(node)

            # GLUE2MappingPolicy
            GLUE2PolicyID = GLUE2ShareID + "/mp/basic"
            node = GLUE2MappingPolicy(GLUE2PolicyID, GLUE2ShareID, GLUE2ServiceID)
            node.init_as_default().add({
                'GLUE2PolicyID': [GLUE2PolicyID],
                'GLUE2EntityCreationTime': [GLUE2EntityCreationTime],
                'GLUE2PolicyRule': sa_data["approachableRules"],
                'GLUE2MappingPolicyShareForeignKey': [GLUE2ShareID]
            })
            if "*" in sa_data["voname"]:
                node.add({'GLUE2PolicyUserDomainForeignKey': ["anonymous"]})
            else:
                node.add({'GLUE2PolicyUserDomainForeignKey': [sa_data["voname"]]})
            nodes.append(node)
            
            # Glue2StorageShareCapacities

            if sa_data["total-space"] > 0: 
                # Glue2StorageShareCapacity online
                GLUE2StorageShareCapacityID = GLUE2ShareID + "/disk"
                node = GLUE2StorageShareCapacity(GLUE2StorageShareCapacityID, GLUE2ShareID, GLUE2ServiceID)
                node.init_as_default().add({
                    'GLUE2StorageShareCapacityID': [GLUE2StorageShareCapacityID],
                    'GLUE2EntityCreationTime': [GLUE2EntityCreationTime],
                    'GLUE2StorageShareCapacityType': ["online"],
                    'GLUE2StorageShareCapacityTotalSize': [str(round_div(sa_data["total-space"],self.FROM_BYTES_TO_GB))], 
                    'GLUE2StorageShareCapacityFreeSize': [str(round_div(sa_data["free-space"],self.FROM_BYTES_TO_GB))], 
                    'GLUE2StorageShareCapacityUsedSize': [str(round_div(sa_data["used-space"],self.FROM_BYTES_TO_GB))], 
                    'GLUE2StorageShareCapacityReservedSize': [str(round_div(sa_data["reserved-space"],self.FROM_BYTES_TO_GB))],
                    'GLUE2StorageShareCapacityStorageShareForeignKey': [GLUE2ShareID]
                })
                nodes.append(node)

            if sa_data["availableNearlineSpace"] > 0: 
                # Glue2StorageShareCapacity nearline
                GLUE2StorageShareCapacityID = GLUE2ShareID + "/tape"
                node = GLUE2StorageShareCapacity(GLUE2StorageShareCapacityID, GLUE2ShareID, GLUE2ServiceID)
                node.init_as_default().add({
                    'GLUE2StorageShareCapacityID': [GLUE2StorageShareCapacityID],
                    'GLUE2EntityCreationTime': [GLUE2EntityCreationTime],
                    'GLUE2StorageShareCapacityType': ["nearline"],
                    'GLUE2StorageShareCapacityTotalSize': [str(round_div(sa_data["availableNearlineSpace"],self.FROM_BYTES_TO_GB))], 
                    'GLUE2StorageShareCapacityFreeSize': [str(round_div(sa_data["availableNearlineSpace"],self.FROM_BYTES_TO_GB))], 
                    'GLUE2StorageShareCapacityUsedSize': [str(0)], 
                    'GLUE2StorageShareCapacityReservedSize': [str(0)],
                    'GLUE2StorageShareCapacityStorageShareForeignKey': [GLUE2ShareID]
                })
                nodes.append(node)

        # Endpoints
        
        # GLUE2AccessPolicyRule
        GLUE2AccessPolicyRule = []
        for vo in stats.get_managed_vos():
            GLUE2AccessPolicyRule.append("vo:" + vo)
        
        # GLUE2EntityOtherInfo
        GLUE2EntityOtherInfo = []
        for protocol in self.get_enabled_protocols(configuration):
            GLUE2EntityOtherInfo.append("SupportedProtocol=" + protocol)        

        # SRM endpoints
        GLUE2EndpointInterfaceName = "SRM"
        GLUE2EndpointInterfaceVersion = "2.2.0"

        # Glue2StorageEndpoint - frontend list
        for frontend_host in configuration.get_frontend_list():
            # Glue2StorageEndpoint SRM
            GLUE2EndpointID = GLUE2ServiceID + "/ep/" + frontend_host + ":" + configuration.get("STORM_FRONTEND_PORT") + "/" + GLUE2EndpointInterfaceName + "/" + GLUE2EndpointInterfaceVersion            
            node = GLUE2StorageEndpoint(GLUE2EndpointID, GLUE2ServiceID)
            node.init_as_default().add({
                'GLUE2EndpointID': [GLUE2EndpointID],
                'GLUE2EntityCreationTime': [GLUE2EntityCreationTime],
                'GLUE2EndpointURL': [configuration.get_public_srm_endpoint()],
                'GLUE2EndpointInterfaceName': [GLUE2EndpointInterfaceName],
                'GLUE2EndpointInterfaceVersion': [GLUE2EndpointInterfaceVersion],
                'GLUE2EndpointTechnology': ["webservice"],
                'GLUE2EndpointQualityLevel': [GLUE2ServiceQualityLevel],
                'GLUE2EndpointServingState': ["production"],
                'GLUE2EndpointCapability': ["data.management.storage"],
                'GLUE2EntityOtherInfo': GLUE2EntityOtherInfo,
                'GLUE2EndpointServiceForeignKey': [GLUE2ServiceID]
            })
            nodes.append(node)

            # Glue2AccessPolicy for the endpoint
            GLUE2PolicyID = GLUE2EndpointID + "/ap/basic"
            node = GLUE2AccessPolicy(GLUE2PolicyID, GLUE2EndpointID, GLUE2ServiceID)
            node.init_as_default().add({
                'GLUE2PolicyID': [GLUE2PolicyID],
                'GLUE2EntityCreationTime': [GLUE2EntityCreationTime],
                'GLUE2AccessPolicyRule': GLUE2AccessPolicyRule,
                'GLUE2AccessPolicyEndpointForeignKey': [GLUE2EndpointID]
            })
            nodes.append(node)

        if configuration.has_gridhttps():

            # Glue2StorageEndpoint - gridhttps list
            for gridhttps_host in configuration.get_gridhttps_list():

                # Glue2StorageEndpoint secure webdav
                GLUE2EndpointInterfaceName = "https"
                GLUE2EndpointInterfaceVersion = "1.1"
                GLUE2EndpointID = GLUE2ServiceID + "/ep/" + gridhttps_host + ":" + configuration.get("STORM_GRIDHTTPS_HTTPS_PORT") + "/" + GLUE2EndpointInterfaceName + "/" + GLUE2EndpointInterfaceVersion

                node = GLUE2StorageEndpoint(GLUE2EndpointID, GLUE2ServiceID)
                node.init_as_default().add({
                    'GLUE2EndpointID': [GLUE2EndpointID],
                    'GLUE2EntityCreationTime': [GLUE2EntityCreationTime],
                    'GLUE2EndpointURL': ["https://" + gridhttps_host + ":" + configuration.get("STORM_GRIDHTTPS_HTTPS_PORT") + "/webdav/"],
                    'GLUE2EndpointInterfaceName': [GLUE2EndpointInterfaceName],
                    'GLUE2EndpointInterfaceVersion': [GLUE2EndpointInterfaceVersion],
                    'GLUE2EndpointTechnology': ["webservice"],
                    'GLUE2EndpointQualityLevel': [GLUE2ServiceQualityLevel],
                    'GLUE2EndpointServingState': ["production"],
                    'GLUE2EndpointCapability': ["data.management.storage", "data.management.transfer"],
                    'GLUE2EntityOtherInfo': ["SupportedProtocol=WebDAV"],
                    'GLUE2EndpointServiceForeignKey': [GLUE2ServiceID]
                })
                nodes.append(node)

                # Glue2AccessPolicy for the endpoint
                GLUE2PolicyID = GLUE2EndpointID + "/ap/basic"
                node = GLUE2AccessPolicy(GLUE2PolicyID, GLUE2EndpointID, GLUE2ServiceID)
                node.init_as_default().add({
                    'GLUE2PolicyID': [GLUE2PolicyID],
                    'GLUE2EntityCreationTime': [GLUE2EntityCreationTime],
                    'GLUE2AccessPolicyRule': GLUE2AccessPolicyRule,
                    'GLUE2AccessPolicyEndpointForeignKey': [GLUE2EndpointID]
                })
                nodes.append(node)

                if configuration.is_HTTP_endpoint_enabled():

                    # Glue2StorageEndpoint anonymous webdav
                    GLUE2EndpointInterfaceName = "http"
                    GLUE2EndpointInterfaceVersion = "1.1"
                    GLUE2EndpointID = GLUE2ServiceID + "/ep/" + gridhttps_host + ":" + configuration.get("STORM_GRIDHTTPS_HTTP_PORT") + "/" + GLUE2EndpointInterfaceName + "/" + GLUE2EndpointInterfaceVersion

                    node = GLUE2StorageEndpoint(GLUE2EndpointID, GLUE2ServiceID)
                    node.init_as_default().add({
                        'GLUE2EndpointID': [GLUE2EndpointID],
                        'GLUE2EntityCreationTime': [GLUE2EntityCreationTime],
                        'GLUE2EndpointURL': ["http://" + gridhttps_host + ":" + configuration.get("STORM_GRIDHTTPS_HTTP_PORT") + "/webdav/"],
                        'GLUE2EndpointInterfaceName': [GLUE2EndpointInterfaceName],
                        'GLUE2EndpointInterfaceVersion': [GLUE2EndpointInterfaceVersion],
                        'GLUE2EndpointTechnology': ["webservice"],
                        'GLUE2EndpointQualityLevel': [GLUE2ServiceQualityLevel],
                        'GLUE2EndpointServingState': ["production"],
                        'GLUE2EndpointCapability': ["data.management.storage", "data.management.transfer"],
                        'GLUE2EntityOtherInfo': ["SupportedProtocol=WebDAV"],
                        'GLUE2EndpointServiceForeignKey': [GLUE2ServiceID]
                    })
                    nodes.append(node)

                    # Glue2AccessPolicy for the endpoint
                    GLUE2PolicyID = GLUE2EndpointID + "/ap/basic"
                    node = GLUE2AccessPolicy(GLUE2PolicyID, GLUE2EndpointID, GLUE2ServiceID)
                    node.init_as_default().add({
                        'GLUE2PolicyID': [GLUE2PolicyID],
                        'GLUE2EntityCreationTime': [GLUE2EntityCreationTime],
                        'GLUE2AccessPolicyRule': ["'ALL'"],
                        'GLUE2AccessPolicyEndpointForeignKey': [GLUE2EndpointID]
                    })
                    nodes.append(node)

        # remove old backup files
        self.delete_backup_files()
        # create LDIF file
        return super(Glue2, self).create_static_ldif_file(self.GLUE2_STATIC_LDIF_FILE, nodes, configuration.is_info_overwrite())

    def get_update_nodes(self, configuration, stats):

        nodes = []

        # Commons
        GLUE2ServiceID = "glue:" + configuration.get("STORM_FRONTEND_PUBLIC_HOST") + "/data"
        
        # Update serving state on Glue2StorageEndpoint(s)

        # SRM endpoints from frontend list
        GLUE2EndpointInterfaceName = "SRM"
        GLUE2EndpointInterfaceVersion = "2.2.0"
        for frontend_host in configuration.get_frontend_list():
            # Glue2StorageEndpoint SRM
            GLUE2EndpointID = GLUE2ServiceID + "/ep/" + frontend_host + ":" + configuration.get("STORM_FRONTEND_PORT") + "/" + GLUE2EndpointInterfaceName + "/" + GLUE2EndpointInterfaceVersion
            nodes.append(GLUE2StorageEndpoint(GLUE2EndpointID, GLUE2ServiceID).add({
                'GLUE2EndpointServingState': [configuration.get("STORM_SERVING_STATE")]
            }))

        if configuration.has_gridhttps():
            # Glue2StorageEndpoint - gridhttps list
            for gridhttps_host in configuration.get_gridhttps_list():
                
                # WebDAV HTTPs endpoint
                GLUE2EndpointInterfaceName = "https"
                GLUE2EndpointInterfaceVersion = "1.1"
                GLUE2EndpointID = GLUE2ServiceID + "/ep/" + gridhttps_host + ":" + configuration.get("STORM_GRIDHTTPS_HTTPS_PORT") + "/" + GLUE2EndpointInterfaceName + "/" + GLUE2EndpointInterfaceVersion
                nodes.append(GLUE2StorageEndpoint(GLUE2EndpointID, GLUE2ServiceID).add({
                    'GLUE2EndpointServingState': [configuration.get("STORM_SERVING_STATE")]
                }))

                if configuration.is_HTTP_endpoint_enabled():

                    # WebDAV HTTP endpoint
                    GLUE2EndpointInterfaceName = "http"
                    GLUE2EndpointInterfaceVersion = "1.1"
                    GLUE2EndpointID = GLUE2ServiceID + "/ep/" + gridhttps_host + ":" + configuration.get("STORM_GRIDHTTPS_HTTP_PORT") + "/" + GLUE2EndpointInterfaceName + "/" + GLUE2EndpointInterfaceVersion
                    nodes.append(GLUE2StorageEndpoint(GLUE2EndpointID, GLUE2ServiceID).add({
                        'GLUE2EndpointServingState': [configuration.get("STORM_SERVING_STATE")]
                    }))

        # Glue2StorageServiceCapacity online
        if stats.get_summary()["total-space"] > 0:
            GLUE2StorageServiceCapacityID = GLUE2ServiceID + "/ssc/disk"
            nodes.append(GLUE2StorageServiceCapacity(GLUE2StorageServiceCapacityID, GLUE2ServiceID).add({ 
                'GLUE2StorageServiceCapacityTotalSize': [str(round_div(stats.get_summary()["total-space"],self.FROM_BYTES_TO_GB))], 
                'GLUE2StorageServiceCapacityFreeSize': [str(round_div(stats.get_summary()["free-space"],self.FROM_BYTES_TO_GB))], 
                'GLUE2StorageServiceCapacityUsedSize': [str(round_div(stats.get_summary()["used-space"],self.FROM_BYTES_TO_GB))], 
                'GLUE2StorageServiceCapacityReservedSize': [str(round_div(stats.get_summary()["reserved-space"],self.FROM_BYTES_TO_GB))]
            }))

        # Glue2StorageServiceCapacity nearline
        if stats.get_summary()["nearline-space"] > 0:
            GLUE2StorageServiceCapacityID = GLUE2ServiceID + "/ssc/tape"
            nodes.append(GLUE2StorageServiceCapacity(GLUE2StorageServiceCapacityID, GLUE2ServiceID).add({ 
                'GLUE2StorageServiceCapacityTotalSize': [str(round_div(stats.get_summary()["nearline-space"],self.FROM_BYTES_TO_GB))], 
                'GLUE2StorageServiceCapacityFreeSize': [str(round_div(stats.get_summary()["nearline-space"],self.FROM_BYTES_TO_GB))],
                'GLUE2StorageServiceCapacityUsedSize': [str(0)], 
                'GLUE2StorageServiceCapacityReservedSize': [str(0)]
            }))

        # Glue2Share, GLUE2MappingPolicy and Glue2StorageShareCapacity for each VFS
        for sa_name,sa_data in stats.get_vfs().items():

            # GLUE2Share
            GLUE2ShareID = GLUE2ServiceID + "/ss/" + sa_data["name"]
            nodes.append(GLUE2StorageShare(GLUE2ShareID, GLUE2ServiceID).add({ 
                'GLUE2StorageShareServingState': [configuration.get("STORM_SERVING_STATE")]
            }))

            # Glue2StorageShareCapacity
            if sa_data["total-space"] > 0:
                GLUE2StorageShareCapacityID = GLUE2ShareID + "/disk"
                nodes.append(GLUE2StorageShareCapacity(GLUE2StorageShareCapacityID, GLUE2ShareID, GLUE2ServiceID).add({ 
                    'GLUE2StorageShareCapacityTotalSize': [str(round_div(sa_data["total-space"],self.FROM_BYTES_TO_GB))], 
                    'GLUE2StorageShareCapacityFreeSize': [str(round_div(sa_data["free-space"],self.FROM_BYTES_TO_GB))], 
                    'GLUE2StorageShareCapacityUsedSize': [str(round_div(sa_data["used-space"],self.FROM_BYTES_TO_GB))], 
                    'GLUE2StorageShareCapacityReservedSize': [str(round_div(sa_data["reserved-space"],self.FROM_BYTES_TO_GB))]
                }))
            if sa_data["nearline-space"] > 0: 
                GLUE2StorageShareCapacityID = GLUE2ShareID + "/tape"
                nodes.append(GLUE2StorageShareCapacity(GLUE2StorageShareCapacityID, GLUE2ShareID, GLUE2ServiceID).add({ 
                    'GLUE2StorageShareCapacityTotalSize': [str(round_div(sa_data["nearline-space"],self.FROM_BYTES_TO_GB))], 
                    'GLUE2StorageShareCapacityFreeSize': [str(round_div(sa_data["nearline-space"],self.FROM_BYTES_TO_GB))], 
                    'GLUE2StorageShareCapacityUsedSize': [str(0)], 
                    'GLUE2StorageShareCapacityReservedSize': [str(0)]
                }))

        return nodes

    def delete_backup_files(self):
        directory = os.path.dirname(self.GLUE2_STATIC_LDIF_FILE)
        removed_list = delete_files(directory, r'static-file-glue2-storm\.ldif\.bkp_.*')
        logging.debug("Removed backup files: [%s]", removed_list)
        return

    def get_enabled_protocols(self, configuration):
        enabled = {}
        for protocol in configuration.get_enabled_protocols():
            enabled[protocol] = self.access_protocols_versions[protocol]
        return enabled

    def remove_old_cron_file_if_exists(self):
        cFile = "/etc/cron.d/glite-info-glue2-dynamic-storm"
        if os.path.isfile(cFile):
            os.remove(cFile)
        return

    def get_service_configuration(self, configuration, vos):
        
        gLite_IS_version = "2.2.0"
        gLite_IS_endpoint = configuration.get_public_srm_endpoint()
        endpoint_capability = str(configuration.get('STORM_ENDPOINT_CAPABILITY'))
        quality_level = QualityLevel_t(int(configuration.get('STORM_ENDPOINT_QUALITY_LEVEL')))
        init_command = "/usr/libexec/storm-dynamic-info-provider/storm-info-provider init-env --version " + gLite_IS_version + " --endpoint " + gLite_IS_endpoint
        status_command = GlueConstants.INFO_SERVICE_SCRIPT + "/glite-info-service-test SRM_V2 && /usr/libexec/storm-dynamic-info-provider/storm-info-provider status"
        get_owner = "echo " + "; echo ".join(vos)
        get_acbr = "echo VO:" + "; echo VO:".join(vos)

        return {
            "init": init_command,
            "service_type": "SRM",
            "get_version": "echo \"" + gLite_IS_version + "\"",
            "get_endpoint": "echo \"" + gLite_IS_endpoint + "\"",
            "WSDL_URL": "http://sdm.lbl.gov/srm-wg/srm.v2.2.wsdl",
            "semantics_URL": "http://sdm.lbl.gov/srm-wg/doc/SRM.v2.2.html",
            "get_starttime": "perl -e '@st=stat(\"/var/run/storm-backend-server.pid\");print \"@st[10]\\n\";'",
            "get_capabilities": "echo \"" + endpoint_capability + "\"",
            "get_implementor": "echo \"emi\"",
            "get_implementationname": "echo \"StoRM\"",
            "get_implementationversion": "rpm -qa | grep storm-backend-server | cut -d- -f4",
            "get_qualitylevel": "echo \"" + str(quality_level) + "\"",
            "get_servingstate": "echo 4",
            "get_data": "echo",
            "get_services": "echo",
            "get_status": status_command,
            "get_owner": get_owner,
            "get_acbr": get_acbr
        }
