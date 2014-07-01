import logging
import stat
import pwd
import grp
import os
import re
import time

from sets import Set

from utils import *

INFO_SERVICE_CONFIG = "/etc/glite/info/service"
INFO_SERVICE_SCRIPT = "/usr/bin"
INFO_PROVIDER_PATH = "/var/lib/bdii/gip/provider"
INFO_LDIF_PATH = "/var/lib/bdii/gip/ldif"
INFO_PLUGIN_PATH = "/var/lib/bdii/gip/plugin"

class Glue2:

    TEMPLATES_DIR = "/etc/storm/info-provider/templates/glue2"

    GLUE2_INFO_SERVICE = INFO_SERVICE_SCRIPT + "/glite-info-glue2-simple"
    GLUE2_SERVICE_FILE = INFO_PROVIDER_PATH + "/service-glue2-srm-storm-v2"
    GLUE2_SERVICE_CONFIG_FILE = INFO_SERVICE_CONFIG + "/glite-info-service-glue2-srm-storm-v2.conf"
    GLUE2_STATIC_LDIF_FILE = INFO_LDIF_PATH + "/static-file-glue2-storm.ldif"
    GLUE2_INFO_PLUGIN_FILE = INFO_PLUGIN_PATH + "/glite-info-glue2-dynamic-storm"

    def __init__(self, configuration, stats):
        self.configuration = configuration
        self.stats = stats
        return

    def init(self):
        # GLUE2_SERVICE_FILE
        logging.debug("Creating %s ...", self.GLUE2_SERVICE_FILE)
        self.create_service_file()
        logging.info("Successfully created %s !", self.GLUE2_SERVICE_FILE)
        # GLUE2_SERVICE_CONFIG_FILE
        logging.debug("Creating %s ...", self.GLUE2_SERVICE_CONFIG_FILE)
        self.create_service_config_file()
        logging.info("Successfully created %s !", self.GLUE2_SERVICE_CONFIG_FILE)
        # GLUE2_STATIC_LDIF_FILE
        logging.debug("Creating %s ...", self.GLUE2_STATIC_LDIF_FILE)
        self.create_static_ldif_file()
        logging.info("Successfully created %s !", self.GLUE2_STATIC_LDIF_FILE)
        # GLUE2_PLUGIN_FILE
        logging.debug("Creating %s ...", self.GLUE2_INFO_PLUGIN_FILE)
        self.create_plugin_file()
        logging.info("Successfully created %s !", self.GLUE2_INFO_PLUGIN_FILE)
        # remove old cron file
        self.remove_old_cron_file_if_exists()
        return

    def create_service_file(self):
        tFile = self.TEMPLATES_DIR + "/service-glue2-srm-storm-v2"
        params = { 
            "info_service": self.GLUE2_INFO_SERVICE,
            "service_config_file": self.GLUE2_SERVICE_CONFIG_FILE,
            "sitename": self.configuration['SITE_NAME'], 
            "srm_endpoint": self.configuration['STORM_FRONTEND_ENDPOINT']
        }
        create_file_from_template(self.GLUE2_SERVICE_FILE, tFile, params)
        # Set execute permissions: chmod +x
        os.chmod(self.GLUE2_SERVICE_FILE, 0755)
        return

    def create_service_config_file(self):
        tFile = self.TEMPLATES_DIR + "/glite-info-service-glue2-srm-storm-v2.conf"
        params = {} 
        params["info_service_script"] = INFO_SERVICE_SCRIPT
        params["endpoint_capability"] = self.configuration['STORM_ENDPOINT_CAPABILITY']
        params["endpoint_quality_level"] = self.configuration['STORM_ENDPOINT_QUALITY_LEVEL']
        params["owner"] = ""
        params["acbr"] = ""
        # compute owner and acbr strings
        for vo_name in self.stats["vos"]:
            params["owner"] += "echo " + vo_name +"; "
            params["acbr"] += "echo VO:" + vo_name +"; "
        create_file_from_template(self.GLUE2_SERVICE_CONFIG_FILE, tFile, params)
        # set owner
        uid = pwd.getpwnam("ldap").pw_uid
        gid = grp.getgrnam("ldap").gr_gid
        os.chown(self.GLUE2_SERVICE_CONFIG_FILE, uid, gid)
        return

    def create_static_ldif_file(self):
        
        # remove old backup files
        for f in os.listdir(os.path.dirname(self.GLUE2_STATIC_LDIF_FILE)):
            if re.search(r'static-file-glue2-storm\.ldif\.bkp_.*',f):
                os.remove(os.path.join(os.path.dirname(self.GLUE2_STATIC_LDIF_FILE), f))
                logging.debug("Removed %s", f)
        
        # Overwrite?
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        self.GLUE2_STATIC_LDIF_FILE_BKP = self.GLUE2_STATIC_LDIF_FILE + ".bkp_" + timestamp
        if self.configuration["STORM_INFO_OVERWRITE"].lower() == "true":
            if os.path.isfile(self.GLUE2_STATIC_LDIF_FILE):
                logging.debug("Overwrite old configuration file %s", self.GLUE2_STATIC_LDIF_FILE)
                os.rename(self.GLUE2_STATIC_LDIF_FILE, self.GLUE2_STATIC_LDIF_FILE_BKP)
                logging.debug("Backup old configuration file in %s", self.GLUE2_STATIC_LDIF_FILE_BKP)
        else:
            logging.debug("Not overwrite old configuration file %s", self.GLUE2_STATIC_LDIF_FILE)
            self.GLUE2_STATIC_LDIF_FILE = self.GLUE2_STATIC_LDIF_FILE + ".yaimnew_" + timestamp
            logging.debug("Create new configuration file in %s", self.GLUE2_STATIC_LDIF_FILE)
        
        # Commons
        params = {}
        params["GLUE2EntityCreationTime"] = time.strftime('%Y-%m-%dT%T')
        params["GLUE2DomainID"] = self.configuration["SITE_NAME"]

        # Glue2StorageService
        tFile = self.TEMPLATES_DIR + "/ldif/Glue2StorageService"
        params["GLUE2ServiceID"] = "glue:" + self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/data"
        params["GLUE2EntityName"] = "storm@" + self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + ":SRM"
        qualitylevels = ["development", "pre-production", "production", "testing"]
        if self.configuration['STORM_ENDPOINT_QUALITY_LEVEL'].lower() in qualitylevels:
            params["GLUE2ServiceQualityLevel"] = self.configuration['STORM_ENDPOINT_QUALITY_LEVEL'].lower()
        else:
            logging.warn("Invalid STORM_ENDPOINT_QUALITY_LEVEL value '%s' - replaced with 'testing'", self.configuration['STORM_ENDPOINT_QUALITY_LEVEL'])
            params["GLUE2ServiceQualityLevel"] = "testing"
        append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)
        
        # Glue2StorageServiceCapacity
        tFile = self.TEMPLATES_DIR + "/ldif/Glue2StorageServiceCapacity"
        
        if self.stats["summary"]["total-space"] > 0:
            # Glue2StorageServiceCapacity online
            params["GLUE2StorageServiceCapacityID"] = params["GLUE2ServiceID"] + "/ssc/disk"
            params["GLUE2StorageServiceCapacityType"] = "online"
            params["GLUE2StorageServiceCapacityTotalSize"] = round_div(self.stats["summary"]["total-space"],1000000000)
            params["GLUE2StorageServiceCapacityFreeSize"] = round_div(self.stats["summary"]["free-space"],1000000000)
            params["GLUE2StorageServiceCapacityUsedSize"] = round_div(self.stats["summary"]["used-space"],1000000000)
            params["GLUE2StorageServiceCapacityReservedSize"] = round_div(self.stats["summary"]["reserved-space"],1000000000)
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)
        
        if self.stats["summary"]["nearline-space"] > 0:
            # Glue2StorageServiceCapacity nearline
            params["GLUE2StorageServiceCapacityID"] = params["GLUE2ServiceID"] + "/ssc/tape"
            params["GLUE2StorageServiceCapacityType"] = "nearline"
            params["GLUE2StorageServiceCapacityTotalSize"] = round_div(self.stats["summary"]["nearline-space"],1000000000)
            params["GLUE2StorageServiceCapacityFreeSize"] = round_div(self.stats["summary"]["nearline-space"],1000000000) # default: we don't have enough info
            params["GLUE2StorageServiceCapacityUsedSize"] = 0
            params["GLUE2StorageServiceCapacityReservedSize"] = 0
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)

        # GLUE2StorageAccessProtocol for each protocol
        protocols = []
        tFile = self.TEMPLATES_DIR + "/ldif/Glue2StorageAccessProtocol"
        if self.configuration["STORM_INFO_FILE_SUPPORT"].upper() == "TRUE":
            protocols.append("file")
            params["GLUE2StorageAccessProtocolType"] = "file"
            params["GLUE2StorageAccessProtocolVersion"] = "1.0.0"        
            params["GLUE2StorageAccessProtocolID"] = params["GLUE2ServiceID"] + "/ap/" + params["GLUE2StorageAccessProtocolType"] + "/" + params["GLUE2StorageAccessProtocolVersion"]
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)

        if self.configuration["STORM_INFO_RFIO_SUPPORT"].upper() == "TRUE":
            protocols.append("rfio")
            params["GLUE2StorageAccessProtocolType"] = "rfio"            
            params["GLUE2StorageAccessProtocolVersion"] = "1.0.0"
            params["GLUE2StorageAccessProtocolID"] = params["GLUE2ServiceID"] + "/ap/" + params["GLUE2StorageAccessProtocolType"] + "/" + params["GLUE2StorageAccessProtocolVersion"]
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)

        if self.configuration["STORM_INFO_GRIDFTP_SUPPORT"].upper() == "TRUE":
            protocols.append("gsiftp")
            params["GLUE2StorageAccessProtocolType"] = "gsiftp"            
            params["GLUE2StorageAccessProtocolVersion"] = "2.0.0"
            params["GLUE2StorageAccessProtocolID"] = params["GLUE2ServiceID"] + "/ap/" + params["GLUE2StorageAccessProtocolType"] + "/" + params["GLUE2StorageAccessProtocolVersion"]
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)

        if self.configuration["STORM_INFO_ROOT_SUPPORT"].upper() == "TRUE":
            protocols.append("root")
            params["GLUE2StorageAccessProtocolType"] = "root"            
            params["GLUE2StorageAccessProtocolVersion"] = "1.0.0"
            params["GLUE2StorageAccessProtocolID"] = params["GLUE2ServiceID"] + "/ap/" + params["GLUE2StorageAccessProtocolType"] + "/" + params["GLUE2StorageAccessProtocolVersion"]
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)

        if self.configuration["STORM_INFO_HTTP_SUPPORT"].upper() == "TRUE":
            protocols.append("http")
            params["GLUE2StorageAccessProtocolType"] = "http"
            params["GLUE2StorageAccessProtocolVersion"] = "1.1.0"
            params["GLUE2StorageAccessProtocolID"] = params["GLUE2ServiceID"] + "/ap/" + params["GLUE2StorageAccessProtocolType"] + "/" + params["GLUE2StorageAccessProtocolVersion"]
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)

        if self.configuration["STORM_INFO_HTTPS_SUPPORT"].upper() == "TRUE":
            protocols.append("https")
            params["GLUE2StorageAccessProtocolType"] = "https"
            params["GLUE2StorageAccessProtocolVersion"] = "1.1.0"
            params["GLUE2StorageAccessProtocolID"] = params["GLUE2ServiceID"] + "/ap/" + params["GLUE2StorageAccessProtocolType"] + "/" + params["GLUE2StorageAccessProtocolVersion"]
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)

        # Glue2StorageManager
        tFile = self.TEMPLATES_DIR + "/ldif/Glue2StorageManager"
        params["GLUE2ManagerID"] = params["GLUE2ServiceID"] + "/m/StoRM"
        append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)

        # Glue2DataStore
        tFile = self.TEMPLATES_DIR + "/ldif/Glue2DataStore"
        
        if self.stats["summary"]["total-space"] > 0:
            # Glue2DataStore disk online
            params["GLUE2ResourceID"] = params["GLUE2ServiceID"] + "/ds/StoRM/disk"
            params["GLUE2DataStoreType"] = "disk"
            params["GLUE2DataStoreLatency"] = "online"
            params["GLUE2DataStoreTotalSize"] = round_div(self.stats["summary"]["total-space"],1000000000)
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)

        if self.stats["summary"]["nearline-space"] > 0:
            # Glue2DataStore tape nearline
            params["GLUE2ResourceID"] = params["GLUE2ServiceID"] + "/ds/StoRM/tape"
            params["GLUE2DataStoreType"] = "tape"
            params["GLUE2DataStoreLatency"] = "nearline"
            params["GLUE2DataStoreTotalSize"] = round_div(self.stats["summary"]["nearline-space"],1000000000)
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)

        vos = Set()

        # Glue2Share, GLUE2MappingPolicy and Glue2StorageShareCapacity for each VFS
        for sa_name in self.stats["sas"]:
            sa_data = self.stats["sas"][sa_name]

            # Glue2Share
            tFile = self.TEMPLATES_DIR + "/ldif/Glue2StorageShare"
            params["vfs"] = sa_data["name"]
            params["voname"] = sa_data["voname"]
            params["GLUE2ShareID"] = params["GLUE2ServiceID"] + "/ss/" + sa_data["name"]
            if "*" in sa_data["voname"]:
                params["GLUE2StorageShareSharingID"] = "dedicated"
            else:
                params["GLUE2StorageShareSharingID"] = ":".join((sa_data["voname"],sa_data["retentionPolicy"],sa_data["accessLatency"]))
            params["GLUE2StorageShareServingState"] = self.configuration['STORM_SERVING_STATE_VALUE']
            #params["GLUE2StorageSharePath"] = sa_data["stfnRoot"][0]
            params["GLUE2StorageShareAccessLatency"] = sa_data["accessLatency"].lower()
            params["GLUE2StorageShareRetentionPolicy"] = sa_data["retentionPolicy"].lower()
            #params["GLUE2StorageShareTag"] = sa_data["name"]
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)

            # GLUE2MappingPolicy
            tFile = self.TEMPLATES_DIR + "/ldif/Glue2MappingPolicy"
            params["GLUE2PolicyID"] = params["GLUE2ShareID"] + "/mp/basic"
            params["GLUE2MappingPolicyRules"] = "GLUE2PolicyRule: " + "\nGLUE2PolicyRule: ".join(sa_data["approachableRules"])
            if "*" in sa_data["voname"]:
                params["GLUE2PolicyUserDomainForeignKey"] = "anonymous"
            else:
                params["GLUE2PolicyUserDomainForeignKey"] = sa_data["voname"]
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)
            
            # Glue2StorageShareCapacity
            tFile = self.TEMPLATES_DIR + "/ldif/Glue2StorageShareCapacity"
            params["GLUE2StorageShareCapacityID"] = params["GLUE2ShareID"] + "/disk"
            params["GLUE2StorageShareCapacityType"] = sa_data["accessLatency"].lower()
            params["GLUE2StorageShareCapacityTotalSize"] = round_div(sa_data["total-space"],1000000000)
            params["GLUE2StorageShareCapacityFreeSize"] = round_div(sa_data["free-space"],1000000000)
            params["GLUE2StorageShareCapacityUsedSize"] = round_div(sa_data["used-space"],1000000000)
            params["GLUE2StorageShareCapacityReservedSize"] = round_div(sa_data["reserved-space"],1000000000)
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)

            if ".*" not in sa_data["voname"]:
                vos.add(sa_data["voname"])
        
        # Glue2StorageEndpoint - frontend list
        frontend_host_list = self.configuration["STORM_FRONTEND_HOST_LIST"].split(',')
        params["GLUE2EndpointInterfaceName"] = "SRM"
        params["GLUE2EndpointInterfaceVersion"] = "2.2.0"
        params["GLUE2EndpointTechnology"] = "webservice"
        params["GLUE2EndpointQualityLevel"] = params["GLUE2ServiceQualityLevel"]
        params["GLUE2EndpointServingState"] = self.configuration['STORM_SERVING_STATE_VALUE'].lower()
        params["GLUE2EndpointCapabilities"] = "GLUE2EndpointCapability: data.management.storage"

        for frontend_host in frontend_host_list:

            # Glue2StorageEndpoint SRM
            tFile = self.TEMPLATES_DIR + "/ldif/Glue2StorageEndpoint"
            params["GLUE2EndpointID"] = params["GLUE2ServiceID"] + "/ep/" + frontend_host + ":" + self.configuration["STORM_FRONTEND_PORT"] + "/" + params["GLUE2EndpointInterfaceName"] + "/" + params["GLUE2EndpointInterfaceVersion"]
            params["GLUE2EndpointURL"] = "httpg://" + frontend_host + ":" + self.configuration["STORM_FRONTEND_PORT"] + "/srm/managerv2"
            params["GLUE2EntityOtherInfos"] = "GLUE2EntityOtherInfo: SupportedProtocol=" + "\nGLUE2EntityOtherInfo: SupportedProtocol=".join(protocols)
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)

            # Glue2AccessPolicy for each endpoint
            tFile = self.TEMPLATES_DIR + "/ldif/Glue2AccessPolicy"
            params["GLUE2PolicyID"] = params["GLUE2EndpointID"] + "/ap/basic"
            params["GLUE2AccessPolicyRules"] = "GLUE2PolicyRule: vo:" + "\nGLUE2PolicyRule: vo:".join(vos)
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)

        if self.configuration['STORM_GRIDHTTPS_ENABLED'].lower() == "true":

            # Glue2StorageEndpoint - gridhttps list
            gridhttps_host_list = self.configuration["STORM_GRIDHTTPS_POOL_LIST"].split(',')
            params["GLUE2EndpointInterfaceName"] = "WebDAV"
            params["GLUE2EndpointInterfaceVersion"] = "1.1"
            params["GLUE2EndpointTechnology"] = "webservice"
            params["GLUE2EndpointQualityLevel"] = params["GLUE2ServiceQualityLevel"]
            params["GLUE2EndpointServingState"] = self.configuration['STORM_SERVING_STATE_VALUE'].lower()
            params["GLUE2EntityOtherInfos"] = "GLUE2EntityOtherInfo: SupportedProtocol=WebDAV"
            params["GLUE2EndpointCapabilities"] = "GLUE2EndpointCapability: " + "\nGLUE2EndpointCapability: ".join(("data.management.storage", "data.management.transfer"))

            for gridhttps_host in gridhttps_host_list:

                if self.configuration['STORM_GRIDHTTPS_HTTP_ENABLED'].lower() == "true" and self.configuration['STORM_INFO_HTTP_SUPPORT'].lower() == "true":

                    # Glue2StorageEndpoint anonymous webdav
                    tFile = self.TEMPLATES_DIR + "/ldif/Glue2StorageEndpoint"
                    params["GLUE2EndpointID"] = params["GLUE2ServiceID"] + "/ep/" + gridhttps_host + ":" + self.configuration["STORM_GRIDHTTPS_HTTP_PORT"] + "/" + params["GLUE2EndpointInterfaceName"] + "/" + params["GLUE2EndpointInterfaceVersion"]
                    params["GLUE2EndpointURL"] = "http://" + gridhttps_host + ":" + self.configuration["STORM_GRIDHTTPS_HTTP_PORT"] + "/webdav/"
                    append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)

                    # Glue2AccessPolicy for each endpoint http
                    tFile = self.TEMPLATES_DIR + "/ldif/Glue2AccessPolicy"
                    params["GLUE2PolicyID"] = params["GLUE2EndpointID"] + "/ap/basic"
                    params["GLUE2AccessPolicyRules"] = "GLUE2PolicyRule: 'ALL'"
                    append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)

                if self.configuration['STORM_INFO_HTTPS_SUPPORT'].lower() == "true":

                    # Glue2StorageEndpoint https
                    tFile = self.TEMPLATES_DIR + "/ldif/Glue2StorageEndpoint"
                    params["GLUE2EndpointID"] = params["GLUE2ServiceID"] + "/ep/" + gridhttps_host + ":" + self.configuration["STORM_GRIDHTTPS_HTTPS_PORT"] + "/" + params["GLUE2EndpointInterfaceName"] + "/" + params["GLUE2EndpointInterfaceVersion"]
                    params["GLUE2EndpointURL"] = "https://" + gridhttps_host + ":" + self.configuration["STORM_GRIDHTTPS_HTTPS_PORT"] + "/webdav/"
                    append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)

                    # Glue2AccessPolicy for each endpoint https
                    tFile = self.TEMPLATES_DIR + "/ldif/Glue2AccessPolicy"
                    params["GLUE2PolicyID"] = params["GLUE2EndpointID"] + "/ap/basic"
                    params["GLUE2AccessPolicyRules"] = "GLUE2PolicyRule: vo:" + "\nGLUE2PolicyRule: vo:".join(vos)
                    append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)

        # set owner
        uid = pwd.getpwnam("ldap").pw_uid
        gid = grp.getgrnam("ldap").gr_gid
        os.chown(self.GLUE2_STATIC_LDIF_FILE, uid, gid)
        os.chmod(self.GLUE2_STATIC_LDIF_FILE, 0644)
        return

    def create_plugin_file(self):

        tFile = self.TEMPLATES_DIR + "/glite-info-glue2-dynamic-storm"
        params = {} 
        params["YaimVariablesFile"] = "/etc/storm/backend-server/storm-yaim-variables.conf"
        create_file_from_template(self.GLUE2_INFO_PLUGIN_FILE, tFile, params)
        # set owner
        uid = pwd.getpwnam("ldap").pw_uid
        gid = grp.getgrnam("ldap").gr_gid
        os.chown(self.GLUE2_INFO_PLUGIN_FILE, uid, gid)
        os.chmod(self.GLUE2_INFO_PLUGIN_FILE, 0755)
        return

    def remove_old_cron_file_if_exists(self):

        cFile = "/etc/cron.d/glite-info-glue2-dynamic-storm"
        if os.path.isfile(cFile):
            os.remove(cFile)
        return
