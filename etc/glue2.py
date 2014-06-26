import logging
import stat
import pwd
import grp
import os
import re
import time

from utils import *

INFO_SERVICE_CONFIG = "/etc/glite/info/service"
INFO_SERVICE_SCRIPT = "/usr/bin"
INFO_PROVIDER_PATH = "/var/lib/bdii/gip/provider"
INFO_LDIF_PATH = "/var/lib/bdii/gip/ldif"
INFO_PLUGIN_PATH = "/var/lib/bdii/gip/plugin"

class Glue2:

    TEMPLATES_DIR = "./glue2" # "/etc/storm/info-provider/templates/glue2"

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
        logging.info("Creating %s ...", self.GLUE2_SERVICE_FILE)
        self.create_service_file()
        logging.info("Successfully created %s !", self.GLUE2_SERVICE_FILE)
        # GLUE2_SERVICE_CONFIG_FILE
        logging.info("Creating %s ...", self.GLUE2_SERVICE_CONFIG_FILE)
        self.create_service_config_file()
        logging.info("Successfully created %s !", self.GLUE2_SERVICE_CONFIG_FILE)
        # GLUE2_STATIC_LDIF_FILE
        logging.info("Creating %s ...", self.GLUE2_STATIC_LDIF_FILE)
        self.create_static_ldif_file()
        logging.info("Successfully created %s !", self.GLUE2_STATIC_LDIF_FILE)
        # GLUE2_PLUGIN_FILE
        logging.info("Creating %s ...", self.GLUE2_INFO_PLUGIN_FILE)
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
        # Glue2StorageService
        tFile = self.TEMPLATES_DIR + "/ldif/Glue2StorageService"
        params = {}
        params["GLUE2ServiceId"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"]
        params["GLUE2EntityCreationTime"] = time.strftime('%Y-%m-%dT%TZ')
        params["GLUE2ServiceCapability"] = self.configuration['STORM_ENDPOINT_CAPABILITY']
        params["GLUE2ServiceQualityLevel"] = self.configuration['STORM_ENDPOINT_QUALITY_LEVEL']
        params["GLUE2ServiceStatusInfo"] = "http://" + self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/get-status"
        params["GLUE2ServiceAdminDomainForeignKey"] = self.configuration['MY_DOMAIN']
        create_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)
        # Glue2StorageServiceCapacityId online
        tFile = self.TEMPLATES_DIR + "/ldif/Glue2StorageServiceCapacityId"
        params = {}
        params["GLUE2ServiceId"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"]
        params["GLUE2StorageServiceCapacityId"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/capacity/online"
        params["GLUE2StorageServiceCapacityType"] = "online"
        params["GLUE2StorageServiceCapacityTotalSize"] = round_div(self.stats["summary"]["total-space"],1000000000)
        params["GLUE2StorageServiceCapacityFreeSize"] = round_div(self.stats["summary"]["free-space"],1000000000)
        params["GLUE2StorageServiceCapacityUsedSize"] = round_div(self.stats["summary"]["used-space"],1000000000)
        params["GLUE2StorageServiceCapacityReservedSize"] = round_div(self.stats["summary"]["reserved-space"],1000000000)
        append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)
        # Glue2StorageServiceCapacityId nearline
        params["GLUE2StorageServiceCapacityType"] = "nearline"
        params["GLUE2StorageServiceCapacityId"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/capacity/nearline"
        params["GLUE2StorageServiceCapacityTotalSize"] = round_div(self.stats["summary"]["nearline-space"],1000000000)
        params["GLUE2StorageServiceCapacityFreeSize"] = 0
        params["GLUE2StorageServiceCapacityUsedSize"] = 0
        params["GLUE2StorageServiceCapacityReservedSize"] = 0
        append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)
        # Glue2EndpointId
        tFile = self.TEMPLATES_DIR + "/ldif/Glue2EndpointId"
        params = {}
        params["GLUE2EndpointId"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/srm/2.2.0"
        params["GLUE2ServiceId"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"]
        params["GLUE2EndpointCapability"] = self.configuration['STORM_ENDPOINT_CAPABILITY']
        params["GLUE2EndpointURL"] = self.configuration["STORM_FRONTEND_ENDPOINT"]
        params["GLUE2EndpointQualityLevel"] = self.configuration['STORM_ENDPOINT_QUALITY_LEVEL']
        params["GLUE2EndpointServingState"] = self.configuration['STORM_SERVING_STATE_VALUE']
        params["GLUE2EndpointServiceForeignKey"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"]
        params["GLUE2StorageEndpointStorageServiceForeignKey"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"]
        append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)
        # Glue2ManagerId
        tFile = self.TEMPLATES_DIR + "/ldif/Glue2ManagerId"
        params = {}
        params["GLUE2ManagerId"] = self.configuration["STORM_BACKEND_HOST"] + "/manager"
        params["GLUE2ServiceId"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"]
        params["GLUE2ManagerServiceForeignKey"] = self.configuration["STORM_BACKEND_HOST"]
        params["GLUE2StorageManagerStorageServiceForeignKey"] = self.configuration["STORM_BACKEND_HOST"]    
        append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)

        for sa_name in self.stats["sas"]:
            sa_data = self.stats["sas"][sa_name]
            params = {}
            # Glue2PolicyID
            tFile = self.TEMPLATES_DIR + "/ldif/Glue2PolicyID"
            params["GLUE2PolicyID"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/srm/2.2.0/ap"
            params["GLUE2EndpointId"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/srm/2.2.0"
            params["GLUE2ServiceId"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"]
            params["GLUE2PolicyRule"] = "VO:" + sa_data["voname"]
            params["GLUE2PolicyUserDomainForeignKey"] = sa_data["voname"]
            params["GLUE2AccessPolicyEndpointForeignKey"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/srm/2.2.0/ap"
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)
            # Glue2ShareID
            tFile = self.TEMPLATES_DIR + "/ldif/Glue2ShareID"
            params["vfs"] = sa_data["name"]
            params["voname"] = sa_data["voname"]
            params["GLUE2ShareId"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/" + sa_data["name"]
            params["GLUE2ShareDescription"] = "Share for " + sa_data["voname"]
            params["GLUE2StorageShareServingState"] = self.configuration['STORM_SERVING_STATE_VALUE']
            params["GLUE2StorageSharePath"] = sa_data["stfnRoot"][0]
            params["GLUE2StorageShareSharingID"] = ":".join((sa_data["voname"],sa_data["retentionPolicy"],sa_data["accessLatency"]))
            params["GLUE2StorageShareAccessLatency"] = sa_data["accessLatency"]
            params["GLUE2StorageShareRetentionPolicy"] = sa_data["retentionPolicy"]
            params["GLUE2StorageShareTag"] = sa_data["name"]
            params["GLUE2ShareServiceForeignKey"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"]
            params["GLUE2StorageShareStorageServiceForeignKey"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/" + sa_data["name"]
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)
            # Glue2StorageShareCapacityID
            tFile = self.TEMPLATES_DIR + "/ldif/Glue2StorageShareCapacityID"
            params["GLUE2StorageShareCapacityID"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/" + sa_data["name"] + "/capacity"
            params["GLUE2StorageShareCapacityType"] = sa_data["accessLatency"]
            params["GLUE2StorageShareCapacityTotalSize"] = round_div(sa_data["total-space"] + sa_data["availableNearlineSpace"],1000000000)
            params["GLUE2StorageShareCapacityFreeSize"] = round_div(sa_data["free-space"],1000000000)
            params["GLUE2StorageShareCapacityUsedSize"] = round_div(sa_data["used-space"],1000000000)
            params["GLUE2StorageShareCapacityReservedSize"] = round_div(sa_data["reserved-space"],1000000000)
            params["GLUE2StorageShareCapacityStorageShareForeignKey"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/" + sa_data["name"] + "/capacity"
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)
        
        # GLUE2StorageAccessProtocolID for each protocol
        tFile = self.TEMPLATES_DIR + "/ldif/Glue2StorageAccessProtocolID"
        params = {}
        params["GLUE2ServiceId"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"]
        if self.configuration["STORM_INFO_FILE_SUPPORT"].upper() == "TRUE":
            params["GLUE2StorageAccessProtocolType"] = "file"            
            params["GLUE2StorageAccessProtocolID"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/" + params["GLUE2StorageAccessProtocolType"]
            params["GLUE2StorageAccessProtocolMaxStreams"] = 1
            params["GLUE2StorageAccessProtocolVersion"] = "1.0.0"
            params["GLUE2StorageAccessProtocolStorageServiceForeignKey"] = params["GLUE2StorageAccessProtocolID"]
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)
        if self.configuration["STORM_INFO_RFIO_SUPPORT"].upper() == "TRUE":
            params["GLUE2StorageAccessProtocolType"] = "rfio"            
            params["GLUE2StorageAccessProtocolID"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/" + params["GLUE2StorageAccessProtocolType"]
            params["GLUE2StorageAccessProtocolMaxStreams"] = 1
            params["GLUE2StorageAccessProtocolVersion"] = "1.0.0"
            params["GLUE2StorageAccessProtocolStorageServiceForeignKey"] = params["GLUE2StorageAccessProtocolID"]
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)
        if self.configuration["STORM_INFO_GRIDFTP_SUPPORT"].upper() == "TRUE":
            params["GLUE2StorageAccessProtocolType"] = "gsiftp"            
            params["GLUE2StorageAccessProtocolID"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/" + params["GLUE2StorageAccessProtocolType"]
            params["GLUE2StorageAccessProtocolMaxStreams"] = 10
            params["GLUE2StorageAccessProtocolVersion"] = "2.0.0"
            params["GLUE2StorageAccessProtocolStorageServiceForeignKey"] = params["GLUE2StorageAccessProtocolID"]
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)
        if self.configuration["STORM_INFO_ROOT_SUPPORT"].upper() == "TRUE":
            params["GLUE2StorageAccessProtocolType"] = "root"            
            params["GLUE2StorageAccessProtocolID"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/" + params["GLUE2StorageAccessProtocolType"]
            params["GLUE2StorageAccessProtocolMaxStreams"] = 1
            params["GLUE2StorageAccessProtocolVersion"] = "1.0.0"
            params["GLUE2StorageAccessProtocolStorageServiceForeignKey"] = params["GLUE2StorageAccessProtocolID"]
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)
        if self.configuration["STORM_INFO_HTTP_SUPPORT"].upper() == "TRUE":
            params["GLUE2StorageAccessProtocolType"] = "http"            
            params["GLUE2StorageAccessProtocolID"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/" + params["GLUE2StorageAccessProtocolType"]
            params["GLUE2StorageAccessProtocolMaxStreams"] = 1
            params["GLUE2StorageAccessProtocolVersion"] = "1.1.0"
            params["GLUE2StorageAccessProtocolStorageServiceForeignKey"] = params["GLUE2StorageAccessProtocolID"]
            append_file_from_template(self.GLUE2_STATIC_LDIF_FILE, tFile, params)
        if self.configuration["STORM_INFO_HTTPS_SUPPORT"].upper() == "TRUE":
            params["GLUE2StorageAccessProtocolType"] = "https"            
            params["GLUE2StorageAccessProtocolID"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + "/" + params["GLUE2StorageAccessProtocolType"]
            params["GLUE2StorageAccessProtocolMaxStreams"] = 1
            params["GLUE2StorageAccessProtocolVersion"] = "1.1.0"
            params["GLUE2StorageAccessProtocolStorageServiceForeignKey"] = params["GLUE2StorageAccessProtocolID"]
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
