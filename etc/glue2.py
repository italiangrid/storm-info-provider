import logging
import pwd
import grp
import time
import os
import re

from glueutils import *
from sets import Set
from utils import *

class Glue2(Glue):

    FROM_BYTES_TO_GB = 1000000000
    FROM_BYTES_TO_KB = 1000

    GLUE2_INFO_SERVICE = GlueConstants.INFO_SERVICE_SCRIPT + "/glite-info-glue2-simple"
    GLUE2_SERVICE_FILE = GlueConstants.INFO_PROVIDER_PATH + "/service-glue2-srm-storm-v2"
    GLUE2_SERVICE_CONFIG_FILE = GlueConstants.INFO_SERVICE_CONFIG + "/glite-info-service-glue2-srm-storm-v2.conf"
    GLUE2_STATIC_LDIF_FILE = GlueConstants.INFO_LDIF_PATH + "/static-file-glue2-storm.ldif"
    GLUE2_INFO_PLUGIN_FILE = GlueConstants.INFO_PLUGIN_PATH + "/glite-info-glue2-dynamic-storm"

    def __init__(self):
        self.creation_time = time.strftime('%Y-%m-%dT%T')
        self.baseDN = "GLUE2GroupID=resource,o=glue"
        self.access_protocols_versions = { 
            'file': '1.0.0', 
            'rfio': '1.0.0', 
            'gsiftp': '2.0.0', 
            'root': '1.0.0', 
            'http': '1.1.0', 
            'https': '1.1.0' 
        }
        self.quality_levels = ["development", "pre-production", "production", "testing"]
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
        content = self.get_service_configuration(configuration, self.get_vos(stats["sas"]))
        content['get_servingstate'] = "echo " + str(configuration["STORM_SERVING_STATE"])
        super(Glue2, self).create_service_config_file(self.GLUE2_SERVICE_CONFIG_FILE, content)
        # generates the updater node list
        node_list = self.get_update_nodes(configuration, stats)
        # print LDIF
        return super(Glue2, self).print_update_ldif(node_list)

    def create_service_file(self, configuration):
        params = []
        params.append(configuration['SITE_NAME'])
        params.append("httpg://" + configuration["STORM_FRONTEND_PUBLIC_HOST"] + ":" + configuration["STORM_FRONTEND_PORT"] + configuration["STORM_FRONTEND_PATH"])        
        return super(Glue2, self).create_service_file(self.GLUE2_SERVICE_FILE, self.GLUE2_INFO_SERVICE, self.GLUE2_SERVICE_CONFIG_FILE, params)

    def create_service_config_file(self, configuration, stats):
        content = self.get_service_configuration(configuration, self.get_vos(stats["sas"]))
        return super(Glue2, self).create_service_config_file(self.GLUE2_SERVICE_CONFIG_FILE, content)

    def create_plugin_file(self):
        params = ["/etc/storm/backend-server/storm-yaim-variables.conf"]
        info_service = "/usr/libexec/storm-dynamic-info-provider/glite-info-glue2-dynamic-storm"
        return super(Glue2, self).create_plugin_file(self.GLUE2_INFO_PLUGIN_FILE, info_service, params)

    def create_static_ldif_file(self, configuration, stats):

        node_list = []

        # Glue2StorageService
        GLUE2DomainID = configuration["SITE_NAME"]
        GLUE2ServiceID = "glue:" + configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/data"
        (dn, entry) = self.get_GLUE2StorageService({
            'GLUE2ServiceID': GLUE2ServiceID,
            'GLUE2DomainID': GLUE2DomainID,
            'GLUE2ServiceQualityLevel': self.quality_levels[int(configuration['STORM_ENDPOINT_QUALITY_LEVEL'])]
        })
        node_list.append({ "dn": dn, "entries": entry })

        # Glue2StorageServiceCapacity online
        if stats["summary"]["total-space"] > 0:
            (dn, entry) = self.get_GLUE2StorageServiceCapacity({
                'GLUE2StorageServiceCapacityID': GLUE2ServiceID + "/ssc/disk", 
                'GLUE2ServiceID': GLUE2ServiceID,
                'GLUE2StorageServiceCapacityType': "online", 
                'GLUE2StorageServiceCapacityTotalSize': round_div(stats["summary"]["total-space"],self.FROM_BYTES_TO_GB), 
                'GLUE2StorageServiceCapacityFreeSize': round_div(stats["summary"]["free-space"],self.FROM_BYTES_TO_GB), 
                'GLUE2StorageServiceCapacityUsedSize': round_div(stats["summary"]["used-space"],self.FROM_BYTES_TO_GB), 
                'GLUE2StorageServiceCapacityReservedSize': round_div(stats["summary"]["reserved-space"],self.FROM_BYTES_TO_GB)
            })
            node_list.append({ "dn": dn, "entries": entry })

        # Glue2StorageServiceCapacity nearline
        if stats["summary"]["nearline-space"] > 0:
            (dn, entry) = self.get_GLUE2StorageServiceCapacity({
                'GLUE2StorageServiceCapacityID': GLUE2ServiceID + "/ssc/tape", 
                'GLUE2ServiceID': GLUE2ServiceID,
                'GLUE2StorageServiceCapacityType': "nearline", 
                'GLUE2StorageServiceCapacityTotalSize': round_div(stats["summary"]["nearline-space"],self.FROM_BYTES_TO_GB), 
                'GLUE2StorageServiceCapacityFreeSize': round_div(stats["summary"]["nearline-space"],self.FROM_BYTES_TO_GB), 
                'GLUE2StorageServiceCapacityUsedSize': 0, 
                'GLUE2StorageServiceCapacityReservedSize': 0
            })
            node_list.append({ "dn": dn, "entries": entry })

        # GLUE2StorageAccessProtocol for each protocol
        protocol_versions = self.get_enabled_protocols(configuration)
        for protocol in protocol_versions:
            (dn, entry) = self.get_GLUE2StorageAccessProtocol({
                'GLUE2StorageAccessProtocolID': GLUE2ServiceID + "/ap/" + protocol + "/" + protocol_versions[protocol], 
                'GLUE2ServiceID': GLUE2ServiceID, 
                'GLUE2StorageAccessProtocolType': protocol, 
                'GLUE2StorageAccessProtocolVersion': protocol_versions[protocol]
            })
            node_list.append({ "dn": dn, "entries": entry })

        # Glue2StorageManager
        GLUE2ManagerID = GLUE2ServiceID + "/m/StoRM"
        (dn, entry) = self.get_GLUE2StorageManager({
            'GLUE2ManagerID': GLUE2ManagerID, 
            'GLUE2ServiceID': GLUE2ServiceID                                                
        })
        node_list.append({ "dn": dn, "entries": entry })

        # Glue2DataStore
        if stats["summary"]["total-space"] > 0:
            # Glue2DataStore disk online
            (dn, entry) = self.get_GLUE2DataStore({
                'GLUE2ResourceID': GLUE2ServiceID + "/ds/StoRM/disk",
                'GLUE2ManagerID': GLUE2ManagerID, 
                'GLUE2ServiceID': GLUE2ServiceID, 
                'GLUE2DataStoreType': "disk", 
                'GLUE2DataStoreLatency': "online", 
                'GLUE2DataStoreTotalSize': round_div(stats["summary"]["total-space"],self.FROM_BYTES_TO_GB)
            })
            node_list.append({ "dn": dn, "entries": entry })

        if stats["summary"]["nearline-space"] > 0:
            # Glue2DataStore tape nearline
            (dn, entry) = self.get_GLUE2DataStore({
                'GLUE2ResourceID': GLUE2ServiceID + "/ds/StoRM/tape",
                'GLUE2ManagerID': GLUE2ManagerID, 
                'GLUE2ServiceID': GLUE2ServiceID, 
                'GLUE2DataStoreType': "tape", 
                'GLUE2DataStoreLatency': "nearline", 
                'GLUE2DataStoreTotalSize': round_div(stats["summary"]["nearline-space"],self.FROM_BYTES_TO_GB)
            })
            node_list.append({ "dn": dn, "entries": entry })

        # Glue2Share, GLUE2MappingPolicy and Glue2StorageShareCapacity for each VFS
        for sa_name in stats["sas"]:
            sa_data = stats["sas"][sa_name]

            # GLUE2Share
            GLUE2ShareID = GLUE2ServiceID + "/ss/" + sa_data["name"]
            sharingID = ":".join((sa_data["voname"],sa_data["retentionPolicy"],sa_data["accessLatency"]))
            if "*" in sa_data["voname"]:
                sharingID = "dedicated"                
            (dn, entry) = self.get_GLUE2StorageShare({
                'GLUE2ShareID': GLUE2ShareID, 
                'GLUE2ServiceID': GLUE2ServiceID, 
                'GLUE2StorageShareAccessLatency': sa_data["accessLatency"].lower(), 
                'GLUE2StorageShareRetentionPolicy': sa_data["retentionPolicy"].lower(), 
                'GLUE2StorageShareServingState': "production", 
                'GLUE2StorageShareSharingID': sharingID 
            })
            node_list.append({ "dn": dn, "entries": entry })

            # GLUE2MappingPolicy
            user_domain = sa_data["voname"]
            if "*" in sa_data["voname"]:
                user_domain = "anonymous" 
            (dn, entry) = self.get_GLUE2MappingPolicy({
                'GLUE2PolicyID': GLUE2ShareID + "/mp/basic", 
                'GLUE2ShareID': GLUE2ShareID,
                'GLUE2ServiceID': GLUE2ServiceID,
                'GLUE2UserDomainID': user_domain,
                'GLUE2PolicyRule': sa_data["approachableRules"]
            })
            node_list.append({ "dn": dn, "entries": entry })
            
            # Glue2StorageShareCapacity
            (dn, entry) = self.get_GLUE2StorageShareCapacity({
                'GLUE2StorageShareCapacityID': GLUE2ShareID + "/disk", 
                'GLUE2ShareID': GLUE2ShareID, 
                'GLUE2ServiceID': GLUE2ServiceID, 
                'GLUE2StorageShareCapacityType': sa_data["accessLatency"].lower(),
                'GLUE2StorageShareCapacityTotalSize': round_div(sa_data["total-space"],self.FROM_BYTES_TO_GB), 
                'GLUE2StorageShareCapacityFreeSize': round_div(sa_data["free-space"],self.FROM_BYTES_TO_GB), 
                'GLUE2StorageShareCapacityUsedSize': round_div(sa_data["used-space"],self.FROM_BYTES_TO_GB), 
                'GLUE2StorageShareCapacityReservedSize': round_div(sa_data["reserved-space"],self.FROM_BYTES_TO_GB)
            })
            node_list.append({ "dn": dn, "entries": entry })

        vos = self.get_vos(stats["sas"])

        # Glue2StorageEndpoint - frontend list
        frontend_host_list = configuration["STORM_FRONTEND_HOST_LIST"].split(',')
        
        # Endpoints
        
        # GLUE2AccessPolicyRule
        GLUE2AccessPolicyRule = []
        for vo in vos:
            GLUE2AccessPolicyRule.append("vo:" + vo)
        
        # GLUE2EntityOtherInfo
        GLUE2EntityOtherInfo = []
        for protocol in protocol_versions:
            GLUE2EntityOtherInfo.append("SupportedProtocol=" + protocol)        

        for frontend_host in frontend_host_list:
            # Glue2StorageEndpoint SRM
            GLUE2EndpointID = GLUE2ServiceID + "/ep/" + frontend_host + ":" + configuration["STORM_FRONTEND_PORT"] + "/" + srm_params['GLUE2EndpointInterfaceName'] + "/" + srm_params['GLUE2EndpointInterfaceVersion']            
            (dn, entry) = self.get_GLUE2StorageEndpoint({
                'GLUE2EndpointID': GLUE2EndpointID,
                'GLUE2EndpointURL': "httpg://" + frontend_host + ":" + configuration["STORM_FRONTEND_PORT"] + configuration["STORM_FRONTEND_PATH"],
                'GLUE2EndpointInterfaceName': "SRM",
                'GLUE2EndpointInterfaceVersion': "2.2.0",
                'GLUE2EndpointTechnology': "webservice",
                'GLUE2EndpointQualityLevel': self.quality_levels[int(configuration['STORM_ENDPOINT_QUALITY_LEVEL'])],
                'GLUE2EndpointServingState': "production",
                'GLUE2EndpointCapability': ["data.management.storage"],
                'GLUE2EntityOtherInfo': GLUE2EntityOtherInfo 
            })
            node_list.append({ "dn": dn, "entries": entry })
            
            # Glue2AccessPolicy for the endpoint
            (dn, entry) = self.get_GLUE2AccessPolicy({
                'GLUE2PolicyID': GLUE2EndpointID + "/ap/basic",
                'GLUE2EndpointID': GLUE2EndpointID,
                'GLUE2ServiceID': GLUE2ServiceID,
                'GLUE2AccessPolicyRule': GLUE2AccessPolicyRule
            })
            node_list.append({ "dn": dn, "entries": entry })

        if configuration['STORM_GRIDHTTPS_ENABLED'].lower() == "true":

            # Glue2StorageEndpoint - gridhttps list
            gridhttps_host_list = configuration["STORM_GRIDHTTPS_POOL_LIST"].split(',')

            for gridhttps_host in gridhttps_host_list:

                if configuration['STORM_GRIDHTTPS_HTTP_ENABLED'].lower() == "true" and configuration['STORM_INFO_HTTP_SUPPORT'].lower() == "true":

                    # Glue2StorageEndpoint anonymous webdav
                    GLUE2EndpointInterfaceName = "http"
                    GLUE2EndpointInterfaceVersion = "1.1"
                    GLUE2EndpointID = GLUE2ServiceID + "/ep/" + gridhttps_host + ":" + configuration["STORM_GRIDHTTPS_HTTP_PORT"] + "/" + GLUE2EndpointInterfaceName + "/" + GLUE2EndpointInterfaceVersion

                    (dn, entry) = self.get_GLUE2StorageEndpoint({
                        'GLUE2EndpointID': GLUE2EndpointID,
                        'GLUE2ServiceID': GLUE2ServiceID,
                        'GLUE2EndpointInterfaceName': GLUE2EndpointInterfaceName,
                        'GLUE2EndpointInterfaceVersion': GLUE2EndpointInterfaceVersion,
                        'GLUE2EndpointURL': "http://" + gridhttps_host + ":" + configuration["STORM_GRIDHTTPS_HTTP_PORT"] + "/webdav/",
                        'GLUE2EndpointTechnology': "webservice",
                        'GLUE2EndpointQualityLevel': self.quality_levels[int(configuration['STORM_ENDPOINT_QUALITY_LEVEL'])],
                        'GLUE2EndpointServingState': "production",
                        'GLUE2EntityOtherInfo': ["SupportedProtocol=WebDAV"],
                        'GLUE2EndpointCapability': ["data.management.storage", "data.management.transfer"]
                    })
                    node_list.append({ "dn": dn, "entries": entry })

                    # Glue2AccessPolicy for the endpoint
                    (dn, entry) = self.get_GLUE2AccessPolicy({
                        'GLUE2PolicyID': GLUE2EndpointID + "/ap/basic",
                        'GLUE2EndpointID': GLUE2EndpointID,
                        'GLUE2ServiceID': GLUE2ServiceID,
                        'GLUE2AccessPolicyRule': ["'ALL'"]
                    })
                    node_list.append({ "dn": dn, "entries": entry })

                if configuration['STORM_INFO_HTTPS_SUPPORT'].lower() == "true":

                    # Glue2StorageEndpoint secure webdav
                    GLUE2EndpointInterfaceName = "https"
                    GLUE2EndpointInterfaceVersion = "1.1"
                    GLUE2EndpointID = GLUE2ServiceID + "/ep/" + gridhttps_host + ":" + configuration["STORM_GRIDHTTPS_HTTPS_PORT"] + "/" + GLUE2EndpointInterfaceName + "/" + GLUE2EndpointInterfaceVersion

                    (dn, entry) = self.get_GLUE2StorageEndpoint({
                        'GLUE2EndpointID': GLUE2EndpointID,
                        'GLUE2ServiceID': GLUE2ServiceID,
                        'GLUE2EndpointInterfaceName': GLUE2EndpointInterfaceName,
                        'GLUE2EndpointInterfaceVersion': GLUE2EndpointInterfaceVersion,
                        'GLUE2EndpointURL': "https://" + gridhttps_host + ":" + configuration["STORM_GRIDHTTPS_HTTPS_PORT"] + "/webdav/",
                        'GLUE2EndpointTechnology': "webservice",
                        'GLUE2EndpointQualityLevel': self.quality_levels[int(configuration['STORM_ENDPOINT_QUALITY_LEVEL'])],
                        'GLUE2EndpointServingState': "production",
                        'GLUE2EntityOtherInfo': ["SupportedProtocol=WebDAV"],
                        'GLUE2EndpointCapability': ["data.management.storage", "data.management.transfer"]
                    })
                    node_list.append({ "dn": dn, "entries": entry })

                    # Glue2AccessPolicy for the endpoint
                    (dn, entry) = self.get_GLUE2AccessPolicy({
                        'GLUE2PolicyID': GLUE2EndpointID + "/ap/basic",
                        'GLUE2EndpointID': GLUE2EndpointID,
                        'GLUE2ServiceID': GLUE2ServiceID,
                        'GLUE2AccessPolicyRule': GLUE2AccessPolicyRule
                    })
                    node_list.append({ "dn": dn, "entries": entry })

        # remove old backup files
        self.delete_backup_files()
        # create LDIF file
        return super(Glue2, self).create_static_ldif_file(self.GLUE2_STATIC_LDIF_FILE, node_list, configuration["STORM_INFO_OVERWRITE"].lower())

    def get_update_nodes(self, configuration, stats):

        node_list = []
        GLUE2ServiceID = "glue:" + configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/data"
        
        # Update serving state on Glue2StorageEndpoint(s)

        # SRM endpoints from frontend list
        GLUE2EndpointInterfaceName = "SRM"
        GLUE2EndpointInterfaceVersion = "2.2.0"
        frontend_host_list = configuration["STORM_FRONTEND_HOST_LIST"].split(',')
        for frontend_host in frontend_host_list:
            # Glue2StorageEndpoint SRM
            GLUE2EndpointID = GLUE2ServiceID + "/ep/" + frontend_host + ":" + configuration["STORM_FRONTEND_PORT"] + "/" + GLUE2EndpointInterfaceName + "/" + GLUE2EndpointInterfaceVersion
            (dn, entry) = self.get_GLUE2StorageEndpoint_update({
                'GLUE2EndpointID': GLUE2EndpointID, 
                'GLUE2ServiceID': GLUE2ServiceID, 
                'GLUE2EndpointServingState': configuration["STORM_SERVING_STATE"]
            })
            node_list.append({ "dn": dn, "entries": entry })

        if configuration['STORM_GRIDHTTPS_ENABLED'].lower() == "true":
            # Glue2StorageEndpoint - gridhttps list
            gridhttps_host_list = configuration["STORM_GRIDHTTPS_POOL_LIST"].split(',')
            for gridhttps_host in gridhttps_host_list:
                if configuration['STORM_GRIDHTTPS_HTTP_ENABLED'].lower() == "true" and configuration['STORM_INFO_HTTP_SUPPORT'].lower() == "true":

                    # WebDAV HTTP endpoint
                    GLUE2EndpointInterfaceName = "http"
                    GLUE2EndpointInterfaceVersion = "1.1"
                    GLUE2EndpointID = GLUE2ServiceID + "/ep/" + gridhttps_host + ":" + configuration["STORM_GRIDHTTPS_HTTP_PORT"] + "/" + GLUE2EndpointInterfaceName + "/" + GLUE2EndpointInterfaceVersion
                    (dn, entry) = self.get_GLUE2StorageEndpoint_update({
                       'GLUE2EndpointID': GLUE2EndpointID, 
                       'GLUE2ServiceID': GLUE2ServiceID, 
                       'GLUE2EndpointServingState': configuration["STORM_SERVING_STATE"]
                    })
                    node_list.append({ "dn": dn, "entries": entry })

                if configuration['STORM_INFO_HTTPS_SUPPORT'].lower() == "true":

                    # WebDAV HTTPs endpoint
                    GLUE2EndpointInterfaceName = "https"
                    GLUE2EndpointInterfaceVersion = "1.1"
                    GLUE2EndpointID = GLUE2ServiceID + "/ep/" + gridhttps_host + ":" + configuration["STORM_GRIDHTTPS_HTTPS_PORT"] + "/" + GLUE2EndpointInterfaceName + "/" + GLUE2EndpointInterfaceVersion
                    (dn, entry) = self.get_GLUE2StorageEndpoint_update({
                       'GLUE2EndpointID': GLUE2EndpointID, 
                       'GLUE2ServiceID': GLUE2ServiceID, 
                       'GLUE2EndpointServingState': configuration["STORM_SERVING_STATE"]
                    })
                    node_list.append({ "dn": dn, "entries": entry })

        # Glue2StorageServiceCapacity online
        if stats["summary"]["total-space"] > 0:
            (dn, entry) = self.get_GLUE2StorageServiceCapacity_update({
                'GLUE2StorageServiceCapacityID': GLUE2ServiceID + "/ssc/disk", 
                'GLUE2ServiceID': GLUE2ServiceID,
                'GLUE2StorageServiceCapacityTotalSize': round_div(stats["summary"]["total-space"],self.FROM_BYTES_TO_GB), 
                'GLUE2StorageServiceCapacityFreeSize': round_div(stats["summary"]["free-space"],self.FROM_BYTES_TO_GB), 
                'GLUE2StorageServiceCapacityUsedSize': round_div(stats["summary"]["used-space"],self.FROM_BYTES_TO_GB), 
                'GLUE2StorageServiceCapacityReservedSize': round_div(stats["summary"]["reserved-space"],self.FROM_BYTES_TO_GB)
            })
            node_list.append({ "dn": dn, "entries": entry })

        # Glue2StorageServiceCapacity nearline
        if stats["summary"]["nearline-space"] > 0:
            (dn, entry) = self.get_GLUE2StorageServiceCapacity_update({
                'GLUE2StorageServiceCapacityID': GLUE2ServiceID + "/ssc/tape", 
                'GLUE2ServiceID': GLUE2ServiceID,
                'GLUE2StorageServiceCapacityTotalSize': round_div(stats["summary"]["nearline-space"],self.FROM_BYTES_TO_GB), 
                'GLUE2StorageServiceCapacityFreeSize': round_div(stats["summary"]["nearline-space"],self.FROM_BYTES_TO_GB), 
                'GLUE2StorageServiceCapacityUsedSize': 0, 
                'GLUE2StorageServiceCapacityReservedSize': 0
            })
            node_list.append({ "dn": dn, "entries": entry })

        # Glue2Share, GLUE2MappingPolicy and Glue2StorageShareCapacity for each VFS
        for sa_name in stats["sas"]:
            sa_data = stats["sas"][sa_name]

            # GLUE2Share
            GLUE2ShareID = GLUE2ServiceID + "/ss/" + sa_data["name"]
            (dn, entry) = self.get_GLUE2StorageShare_update({
                'GLUE2ShareID': GLUE2ShareID, 
                'GLUE2ServiceID': GLUE2ServiceID, 
                'GLUE2StorageShareServingState': configuration["STORM_SERVING_STATE"]
            })
            node_list.append({ "dn": dn, "entries": entry })
            
            # Glue2StorageShareCapacity
            (dn, entry) = self.get_GLUE2StorageShareCapacity_update({
                'GLUE2StorageShareCapacityID': GLUE2ShareID + "/disk", 
                'GLUE2ShareID': GLUE2ShareID, 
                'GLUE2ServiceID': GLUE2ServiceID, 
                'GLUE2StorageShareCapacityTotalSize': round_div(sa_data["total-space"],self.FROM_BYTES_TO_GB), 
                'GLUE2StorageShareCapacityFreeSize': round_div(sa_data["free-space"],self.FROM_BYTES_TO_GB), 
                'GLUE2StorageShareCapacityUsedSize': round_div(sa_data["used-space"],self.FROM_BYTES_TO_GB), 
                'GLUE2StorageShareCapacityReservedSize': round_div(sa_data["reserved-space"],self.FROM_BYTES_TO_GB)
            })
            node_list.append({ "dn": dn, "entries": entry })

        return node_list

    def delete_backup_files(self):
        directory = os.path.dirname(self.GLUE2_STATIC_LDIF_FILE)
        removed_list = delete_files(directory, r'static-file-glue2-storm\.ldif\.bkp_.*')
        logging.debug("Removed backup files: [%s]", removed_list)
        return

    def get_enabled_protocols(self, configuration):
        enabled = {}
        if configuration["STORM_INFO_FILE_SUPPORT"].lower() == "true":
            enabled["file"] = self.access_protocols_versions["file"]
        if configuration["STORM_INFO_RFIO_SUPPORT"].lower() == "true":
            enabled["rfio"] = self.access_protocols_versions["rfio"]
        if configuration["STORM_INFO_GRIDFTP_SUPPORT"].lower() == "true":
            enabled["gsiftp"] = self.access_protocols_versions["gsiftp"]
        if configuration["STORM_INFO_ROOT_SUPPORT"].lower() == "true":
            enabled["root"] = self.access_protocols_versions["root"]
        if configuration["STORM_INFO_HTTP_SUPPORT"].lower() == "true":
            enabled["http"] = self.access_protocols_versions["http"]
        if configuration["STORM_INFO_HTTPS_SUPPORT"].lower() == "true":
            enabled["https"] = self.access_protocols_versions["https"]
        return enabled

    def get_vos(self, sas):
        vos = Set()
        for sa_name in sas:
            if ".*" not in sas[sa_name]["voname"]:
                vos.add(sas[sa_name]["voname"])
        return vos

    def remove_old_cron_file_if_exists(self):
        cFile = "/etc/cron.d/glite-info-glue2-dynamic-storm"
        if os.path.isfile(cFile):
            os.remove(cFile)
        return

    def get_service_configuration(self, configuration, vos):
        GLITE_INFO_SERVICE_VERSION = "2.2.0"
        GLITE_INFO_SERVICE_ENDPOINT = "httpg://" + configuration["STORM_FRONTEND_PUBLIC_HOST"] + ":" + configuration["STORM_FRONTEND_PORT"] + configuration["STORM_FRONTEND_PATH"]
        QUALITY_LEVEL = self.quality_levels[int(configuration['STORM_ENDPOINT_QUALITY_LEVEL'])]
        STATUS_CMD = GlueConstants.INFO_SERVICE_SCRIPT + "/glite-info-service-test SRM_V2 && /usr/libexec/storm-dynamic-info-provider/storm-info-provider status"
        OWNER = "echo " + "; echo ".join(vos)
        ACBR = "echo VO:" + "; echo VO:".join(vos)
        content = {
            "init": "/usr/libexec/storm-dynamic-info-provider/storm-info-provider init-env --version " + GLITE_INFO_SERVICE_VERSION + " --endpoint " + GLITE_INFO_SERVICE_ENDPOINT,
            "service_type": "SRM",
            "get_version": "echo \"" + GLITE_INFO_SERVICE_VERSION + "\"",
            "get_endpoint": "echo \"" + GLITE_INFO_SERVICE_ENDPOINT + "\"",
            "WSDL_URL": "http://sdm.lbl.gov/srm-wg/srm.v2.2.wsdl",
            "semantics_URL": "http://sdm.lbl.gov/srm-wg/doc/SRM.v2.2.html",
            "get_starttime": "perl -e '@st=stat(\"/var/run/storm-backend-server.pid\");print \"@st[10]\\n\";'",
            "get_capabilities": "echo \"" + str(configuration['STORM_ENDPOINT_CAPABILITY']) + "\"",
            "get_implementor": "echo \"emi\"",
            "get_implementationname": "echo \"StoRM\"",
            "get_implementationversion": "rpm -qa | grep storm-backend-server | cut -d- -f4",
            "get_qualitylevel": "echo \"" + str(QUALITY_LEVEL) + "\"",
            "get_servingstate": "echo 4",
            "get_data": "echo",
            "get_services": "echo",
            "get_status": str(STATUS_CMD),
            "get_owner": str(OWNER),
            "get_acbr": str(ACBR)
        }
        return content

    def check_required_params(self, input_dict, mandatory_list):
        for par_name in mandatory_list:
            if not par_name in input_dict:
                raise ValueError("Missing " + par_name + " parameter!")

    def get_GLUE2StorageService(self, params):
        mandatories = ['GLUE2ServiceID', 'GLUE2AdminDomainID', 'GLUE2ServiceQualityLevel']
        self.check_required_params(params, mandatories)
        dn = "GLUE2ServiceID=" + params['GLUE2ServiceID'] + "," + self.baseDN
        entry = { 
            'objectClass': ['GLUE2Service', 'GLUE2StorageService'],
            'GLUE2EntityCreationTime': [self.creation_time],
            'GLUE2ServiceID': [params['GLUE2ServiceID']],
            'GLUE2ServiceType': ['storm'],
            'GLUE2ServiceQualityLevel': [params['GLUE2ServiceQualityLevel']],
            'GLUE2ServiceCapability': ['data.management.storage', 'data.management.transfer'],
            'GLUE2EntityOtherInfo': ['ProfileName=EGI', 'ProfileVersion=1.0'],
            'GLUE2ServiceAdminDomainForeignKey': [params['GLUE2AdminDomainID']]
        }
        return (dn, entry)

    def get_GLUE2StorageServiceCapacity(self, params):
        mandatories = ['GLUE2StorageServiceCapacityID', 'GLUE2ServiceID', 'GLUE2StorageServiceCapacityType', 
            'GLUE2StorageServiceCapacityTotalSize', 'GLUE2StorageServiceCapacityFreeSize', 
            'GLUE2StorageServiceCapacityUsedSize', 'GLUE2StorageServiceCapacityReservedSize']
        self.check_required_params(params, mandatories)
        dn = "GLUE2StorageServiceCapacityID=" + params['GLUE2StorageServiceCapacityID'] + ",GLUE2ServiceID=" + params['GLUE2ServiceID'] + "," + self.baseDN
        entry = { 
            'objectClass': ['GLUE2StorageServiceCapacity'],
            'GLUE2EntityCreationTime': [self.creation_time],
            'GLUE2StorageServiceCapacityID': [params['GLUE2StorageServiceCapacityID']],
            'GLUE2StorageServiceCapacityType': [params['GLUE2StorageServiceCapacityType']],
            'GLUE2StorageServiceCapacityTotalSize': [str(params['GLUE2StorageServiceCapacityTotalSize'])],
            'GLUE2StorageServiceCapacityFreeSize': [str(params['GLUE2StorageServiceCapacityFreeSize'])],
            'GLUE2StorageServiceCapacityUsedSize': [str(params['GLUE2StorageServiceCapacityUsedSize'])],
            'GLUE2StorageServiceCapacityReservedSize': [str(params['GLUE2StorageServiceCapacityReservedSize'])],
            'GLUE2StorageServiceCapacityStorageServiceForeignKey': [params['GLUE2ServiceID']]
        }
        return (dn, entry)

    def get_GLUE2StorageAccessProtocol(self, params):
        mandatories = ['GLUE2StorageAccessProtocolID', 'GLUE2ServiceID', 'GLUE2StorageAccessProtocolType', 
            'GLUE2StorageAccessProtocolVersion']
        self.check_required_params(params, mandatories)
        dn = "GLUE2StorageAccessProtocolID=" + params['GLUE2StorageAccessProtocolID'] + ",GLUE2ServiceID=" + params['GLUE2ServiceID'] + "," + self.baseDN
        entry = { 
            'objectClass': ['GLUE2StorageAccessProtocol'],
            'GLUE2StorageAccessProtocolID': [params['GLUE2StorageAccessProtocolID']],
            'GLUE2EntityCreationTime': [self.creation_time],
            'GLUE2StorageAccessProtocolType': [params['GLUE2StorageAccessProtocolType']],
            'GLUE2StorageAccessProtocolVersion': [params['GLUE2StorageAccessProtocolVersion']],
            'GLUE2StorageAccessProtocolStorageServiceForeignKey': [params['GLUE2ServiceID']]
        }
        return (dn, entry)

    def get_GLUE2StorageManager(self, params):
        mandatories = ['GLUE2ManagerID', 'GLUE2ServiceID']
        self.check_required_params(params, mandatories)
        dn = "GLUE2ManagerID=" + params['GLUE2ManagerID'] + ",GLUE2ServiceID=" + params['GLUE2ServiceID'] + "," + self.baseDN
        entry = { 
            'objectClass': ['GLUE2Manager', 'GLUE2StorageManager'],
            'GLUE2EntityCreationTime': [self.creation_time],
            'GLUE2ManagerID': [params['GLUE2ManagerID']],
            'GLUE2ManagerProductName': ['StoRM'],
            'GLUE2ManagerProductVersion': ["`rpm -q --queryformat='%{VERSION}' storm-backend-server`"],
            'GLUE2StorageManagerStorageServiceForeignKey': [params['GLUE2ServiceID']],
            'GLUE2ManagerServiceForeignKey': [params['GLUE2ServiceID']]
        }
        return (dn, entry)

    def get_GLUE2DataStore(self, params):
        mandatories = ['GLUE2ResourceID', 'GLUE2ManagerID', 'GLUE2ServiceID', 'GLUE2DataStoreType', 
            'GLUE2DataStoreLatency', 'GLUE2DataStoreTotalSize']
        self.check_required_params(params, mandatories)
        dn = "GLUE2ResourceID=" + params['GLUE2ResourceID'] + ",GLUE2ManagerID=" + params['GLUE2ManagerID'] + ",GLUE2ServiceID=" + params['GLUE2ServiceID'] + "," + self.baseDN
        entry = { 
            'objectClass': ['GLUE2DataStore', 'GLUE2Resource'],
            'GLUE2ResourceID': [params['GLUE2ResourceID']],
            'GLUE2EntityCreationTime': [self.creation_time],
            'GLUE2DataStoreType': [params['GLUE2DataStoreType']],
            'GLUE2DataStoreLatency': [params['GLUE2DataStoreLatency']],
            'GLUE2DataStoreTotalSize': [str(params['GLUE2DataStoreTotalSize'])],
            'GLUE2ResourceManagerForeignKey': [params['GLUE2ManagerID']],
            'GLUE2DataStoreStorageManagerForeignKey': [params['GLUE2ManagerID']]
        }
        return (dn, entry)

    def get_GLUE2StorageShare(self, params):
        mandatories = ['GLUE2ShareID', 'GLUE2ServiceID', 'GLUE2StorageShareAccessLatency', 
            'GLUE2StorageShareRetentionPolicy', 'GLUE2StorageShareServingState', 'GLUE2StorageShareSharingID']
        self.check_required_params(params, mandatories)
        dn = "GLUE2ShareID=" + params['GLUE2ShareID'] + ",GLUE2ServiceID=" + params['GLUE2ServiceID'] + "," + self.baseDN
        entry = { 
            'objectClass': ['GLUE2Share', 'GLUE2StorageShare'],
            'GLUE2ShareID': [params['GLUE2ShareID']],
            'GLUE2EntityCreationTime': [self.creation_time],
            'GLUE2ShareServiceForeignKey': [params['GLUE2ServiceID']],
            'GLUE2StorageShareAccessLatency': [params['GLUE2StorageShareAccessLatency']],
            'GLUE2StorageShareRetentionPolicy': [params['GLUE2StorageShareRetentionPolicy']],
            'GLUE2StorageShareServingState': [params['GLUE2StorageShareServingState']],
            'GLUE2StorageShareSharingID': [params['GLUE2StorageShareSharingID']],
            'GLUE2StorageShareExpirationMode': ['neverexpire'],
            'GLUE2StorageShareStorageServiceForeignKey': [params['GLUE2ServiceID']]
        }
        return (dn, entry)

    def get_GLUE2MappingPolicy(self, params):
        mandatories = ['GLUE2PolicyID', 'GLUE2ShareID', 'GLUE2ServiceID', 'GLUE2UserDomainID', 'GLUE2PolicyRule']
        self.check_required_params(params, mandatories)
        dn = "GLUE2PolicyID=" + params['GLUE2PolicyID'] + ",GLUE2ShareID=" + params['GLUE2ShareID'] + ",GLUE2ServiceID=" + params['GLUE2ServiceID'] + "," + self.baseDN
        entry = { 
            'objectClass': ['GLUE2Policy', 'GLUE2MappingPolicy'],
            'GLUE2PolicyID': [params['GLUE2PolicyID']],
            'GLUE2EntityCreationTime': [self.creation_time],
            'GLUE2PolicyScheme': ['basic'],
            'GLUE2PolicyRule': params['GLUE2PolicyRule'],
            'GLUE2MappingPolicyShareForeignKey': [params['GLUE2ShareID']],
            'GLUE2PolicyUserDomainForeignKey': [params['GLUE2UserDomainID']]
        }
        return (dn, entry)

    def get_GLUE2StorageShareCapacity(self, params):
        mandatories = ['GLUE2StorageShareCapacityID', 'GLUE2ShareID', 'GLUE2ServiceID', 'GLUE2StorageShareCapacityType',
            'GLUE2StorageShareCapacityTotalSize', 'GLUE2StorageShareCapacityFreeSize', 'GLUE2StorageShareCapacityUsedSize', 
            'GLUE2StorageShareCapacityReservedSize']
        self.check_required_params(params, mandatories)
        dn = "GLUE2StorageShareCapacityID=" + params['GLUE2StorageShareCapacityID'] + ",GLUE2ShareID=" + params['GLUE2ShareID'] + ",GLUE2ServiceID=" + params['GLUE2ServiceID'] + "," + self.baseDN
        entry = { 
            'objectClass': ['GLUE2StorageShareCapacity'],
            'GLUE2EntityCreationTime': [self.creation_time],
            'GLUE2StorageShareCapacityID': [params['GLUE2StorageShareCapacityID']],
            'GLUE2StorageShareCapacityType': [params['GLUE2StorageShareCapacityType']],
            'GLUE2StorageShareCapacityTotalSize': [str(params['GLUE2StorageShareCapacityTotalSize'])],
            'GLUE2StorageShareCapacityFreeSize': [str(params['GLUE2StorageShareCapacityFreeSize'])],
            'GLUE2StorageShareCapacityUsedSize': [str(params['GLUE2StorageShareCapacityUsedSize'])],
            'GLUE2StorageShareCapacityReservedSize': [str(params['GLUE2StorageShareCapacityReservedSize'])],
            'GLUE2StorageShareCapacityStorageShareForeignKey': [params['GLUE2ShareID']]
        }
        return (dn, entry)

    def get_GLUE2StorageEndpoint(self, params):
        mandatories = ['GLUE2EndpointID', 'GLUE2ServiceID', 'GLUE2EndpointURL', 'GLUE2EntityOtherInfo', 
            'GLUE2EndpointTechnology', 'GLUE2EndpointInterfaceName', 'GLUE2EndpointInterfaceVersion', 
            'GLUE2EndpointQualityLevel', 'GLUE2EndpointServingState', 'GLUE2EndpointCapability']
        self.check_required_params(params, mandatories)
        dn = "GLUE2EndpointID=" + params['GLUE2EndpointID'] + ",GLUE2ServiceID=" + params['GLUE2ServiceID'] + "," + self.baseDN
        entry = {
            'objectClass': ['GLUE2Endpoint', 'GLUE2StorageEndpoint'],
            'GLUE2EntityCreationTime': [self.creation_time],
            'GLUE2EntityOtherInfo': params['GLUE2EntityOtherInfo'],
            'GLUE2EndpointID': [params['GLUE2EndpointID']],
            'GLUE2EndpointURL': [params['GLUE2EndpointURL']],
            'GLUE2EndpointTechnology': [params['GLUE2EndpointTechnology']],
            'GLUE2EndpointInterfaceName': [params['GLUE2EndpointInterfaceName']],
            'GLUE2EndpointInterfaceVersion': [params['GLUE2EndpointInterfaceVersion']],
            'GLUE2EndpointImplementationName': ['StoRM'],
            'GLUE2EndpointImplementationVersion': ["`rpm -q --queryformat='%{VERSION}' storm-backend-server`"],
            'GLUE2EndpointQualityLevel': [params['GLUE2EndpointQualityLevel']],
            'GLUE2EndpointHealthState': ['ok'],
            'GLUE2EndpointServingState': [params['GLUE2EndpointServingState']],
            'GLUE2EndpointIssuerCA': ["`openssl x509 -issuer -noout -in /etc/grid-security/hostcert.pem | sed 's/^[^/]*//'`"],
            'GLUE2EndpointCapability': params['GLUE2EndpointCapability'],
            'GLUE2EndpointServiceForeignKey': [params['GLUE2ServiceID']]
        }
        return (dn, entry)

    def get_GLUE2AccessPolicy(self, params):
        mandatories = ['GLUE2PolicyID', 'GLUE2EndpointID', 'GLUE2ServiceID', 'GLUE2PolicyRule']
        self.check_required_params(params, mandatories)
        dn = "GLUE2PolicyID=" + params['GLUE2PolicyID'] + ",GLUE2EndpointID=" + params['GLUE2EndpointID'] + ",GLUE2ServiceID=" + params['GLUE2ServiceID'] + "," + self.baseDN
        entry = { 
            'objectClass': ['GLUE2Policy', 'GLUE2AccessPolicy'],
            'GLUE2PolicyID': [params['GLUE2PolicyID']],
            'GLUE2EntityCreationTime': [self.creation_time],
            'GLUE2PolicyScheme': ['basic'],
            'GLUE2PolicyRule': params['GLUE2PolicyRule'],
            'GLUE2AccessPolicyEndpointForeignKey': [params['GLUE2EndpointID']]
        }
        return (dn, entry)

    def get_GLUE2StorageEndpoint_update(self, params):
        mandatories = ['GLUE2EndpointID', 'GLUE2ServiceID', 'GLUE2EndpointServingState']
        self.check_required_params(params, mandatories)
        dn = "GLUE2EndpointID=" + params['GLUE2EndpointID'] + ",GLUE2ServiceID=" + params['GLUE2ServiceID'] + "," + self.baseDN
        entry = {
            'GLUE2EndpointServingState': [str(params['GLUE2EndpointServingState'])]
        }
        return (dn, entry)

    def get_GLUE2StorageServiceCapacity_update(self, params):
        mandatories = ['GLUE2StorageServiceCapacityID', 'GLUE2ServiceID',
            'GLUE2StorageServiceCapacityTotalSize', 'GLUE2StorageServiceCapacityFreeSize', 
            'GLUE2StorageServiceCapacityUsedSize', 'GLUE2StorageServiceCapacityReservedSize']
        self.check_required_params(params, mandatories)
        dn = "GLUE2StorageServiceCapacityID=" + params['GLUE2StorageServiceCapacityID'] + ",GLUE2ServiceID=" + params['GLUE2ServiceID'] + "," + self.baseDN
        entry = { 
            'GLUE2StorageServiceCapacityTotalSize': [str(params['GLUE2StorageServiceCapacityTotalSize'])],
            'GLUE2StorageServiceCapacityFreeSize': [str(params['GLUE2StorageServiceCapacityFreeSize'])],
            'GLUE2StorageServiceCapacityUsedSize': [str(params['GLUE2StorageServiceCapacityUsedSize'])],
            'GLUE2StorageServiceCapacityReservedSize': [str(params['GLUE2StorageServiceCapacityReservedSize'])],
        }
        return (dn, entry)

    def get_GLUE2StorageShare_update(self, params):
        mandatories = ['GLUE2ShareID', 'GLUE2ServiceID', 'GLUE2StorageShareServingState']
        self.check_required_params(params, mandatories)
        dn = "GLUE2ShareID=" + params['GLUE2ShareID'] + ",GLUE2ServiceID=" + params['GLUE2ServiceID'] + "," + self.baseDN
        entry = { 
            'GLUE2StorageShareServingState': [str(params['GLUE2StorageShareServingState'])],
        }
        return (dn, entry)

    def get_GLUE2StorageShareCapacity_update(self, params):
        mandatories = ['GLUE2StorageShareCapacityID', 'GLUE2ShareID', 'GLUE2ServiceID', 
            'GLUE2StorageShareCapacityTotalSize', 'GLUE2StorageShareCapacityFreeSize', 
            'GLUE2StorageShareCapacityUsedSize', 'GLUE2StorageShareCapacityReservedSize']
        self.check_required_params(params, mandatories)
        dn = "GLUE2StorageShareCapacityID=" + params['GLUE2StorageShareCapacityID'] + ",GLUE2ShareID=" + params['GLUE2ShareID'] + ",GLUE2ServiceID=" + params['GLUE2ServiceID'] + "," + self.baseDN
        entry = { 
            'GLUE2StorageShareCapacityTotalSize': [str(params['GLUE2StorageShareCapacityTotalSize'])],
            'GLUE2StorageShareCapacityFreeSize': [str(params['GLUE2StorageShareCapacityFreeSize'])],
            'GLUE2StorageShareCapacityUsedSize': [str(params['GLUE2StorageShareCapacityUsedSize'])],
            'GLUE2StorageShareCapacityReservedSize': [str(params['GLUE2StorageShareCapacityReservedSize'])],
        }
        return (dn, entry)