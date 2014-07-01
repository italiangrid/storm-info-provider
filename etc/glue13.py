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

class Glue13:

    TEMPLATES_DIR = "./glue13" # "/etc/storm/info-provider/templates/glue13"

    GLUE13_INFO_SERVICE = INFO_SERVICE_SCRIPT + "/glite-info-service"
    GLUE13_SERVICE_FILE = INFO_PROVIDER_PATH + "/service-srm-storm-v2"
    GLUE13_SERVICE_CONFIG_FILE = INFO_SERVICE_CONFIG + "/glite-info-service-srm-storm-v2.conf"
    GLUE13_STATIC_LDIF_FILE = INFO_LDIF_PATH + "/static-file-storm.ldif"
    GLUE13_INFO_PLUGIN_FILE = INFO_PLUGIN_PATH + "/glite-info-dynamic-storm"

    def __init__(self, configuration, stats):
        self.configuration = configuration
        self.stats = stats
        return

    def init(self):
        # GLUE13_SERVICE_FILE
        logging.debug("Creating %s ...", self.GLUE13_SERVICE_FILE)
        self.create_service_file()
        logging.info("Successfully created %s !", self.GLUE13_SERVICE_FILE)
        # GLUE13_SERVICE_CONFIG_FILE
        logging.debug("Creating %s ...", self.GLUE13_SERVICE_CONFIG_FILE)
        self.create_service_config_file()
        logging.info("Successfully created %s !", self.GLUE13_SERVICE_CONFIG_FILE)
        # GLUE13_STATIC_LDIF_FILE
        logging.debug("Creating %s ...", self.GLUE13_STATIC_LDIF_FILE)
        self.create_static_ldif_file()
        logging.info("Successfully created %s !", self.GLUE13_STATIC_LDIF_FILE)
        # GLUE13_PLUGIN_FILE
        logging.debug("Creating %s ...", self.GLUE13_INFO_PLUGIN_FILE)
        self.create_plugin_file()
        logging.info("Successfully created %s !", self.GLUE13_INFO_PLUGIN_FILE)
        # remove old cron file
        self.remove_old_cron_file_if_exists()
        return

    def create_service_file(self):
        tFile = self.TEMPLATES_DIR + "/service-srm-storm-v2"
        params = { 
            "info_service": self.GLUE13_INFO_SERVICE,
            "service_config_file": self.GLUE13_SERVICE_CONFIG_FILE,
            "sitename": self.configuration['SITE_NAME'], 
            "srm_endpoint": self.configuration['STORM_FRONTEND_ENDPOINT']
        }
        create_file_from_template(self.GLUE13_SERVICE_FILE, tFile, params)
        # Set execute permissions: chmod +x
        os.chmod(self.GLUE13_SERVICE_FILE, 0755)
        return

    def create_service_config_file(self):
        tFile = self.TEMPLATES_DIR + "/glite-info-service-srm-storm-v2.conf"
        params = {} 
        params["info_service_script"] = INFO_SERVICE_SCRIPT
        params["owner"] = ""
        params["acbr"] = ""
        # compute owner and acbr strings
        for vo_name in self.stats["vos"]:
            params["owner"] += "echo " + vo_name +"; "
            params["acbr"] += "echo VO:" + vo_name +"; "
        create_file_from_template(self.GLUE13_SERVICE_CONFIG_FILE, tFile, params)
        # set owner
        uid = pwd.getpwnam("ldap").pw_uid
        gid = grp.getgrnam("ldap").gr_gid
        os.chown(self.GLUE13_SERVICE_CONFIG_FILE, uid, gid)
        return

    def create_static_ldif_file(self):
        # remove old backup files
        for f in os.listdir(os.path.dirname(self.GLUE13_STATIC_LDIF_FILE)):
            if re.search(r'static-file-storm\.ldif\.bkp_.*',f):
                os.remove(os.path.join(os.path.dirname(self.GLUE13_STATIC_LDIF_FILE), f))
                logging.debug("Removed %s", f)
        # Overwrite?
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        self.GLUE13_STATIC_LDIF_FILE_BKP = self.GLUE13_STATIC_LDIF_FILE + ".bkp_" + timestamp
        if self.configuration["STORM_INFO_OVERWRITE"].lower() == "true":
            if os.path.isfile(self.GLUE13_STATIC_LDIF_FILE):
                logging.debug("Overwrite old configuration file %s", self.GLUE13_STATIC_LDIF_FILE)
                os.rename(self.GLUE13_STATIC_LDIF_FILE, self.GLUE13_STATIC_LDIF_FILE_BKP)
                logging.debug("Backup old configuration file in %s", self.GLUE13_STATIC_LDIF_FILE_BKP)
        else:
            logging.debug("Not overwrite old configuration file %s", self.GLUE13_STATIC_LDIF_FILE)
            self.GLUE13_STATIC_LDIF_FILE = self.GLUE13_STATIC_LDIF_FILE + ".yaimnew_" + timestamp
            logging.debug("Create new configuration file in %s", self.GLUE13_STATIC_LDIF_FILE)
        # GlueSE
        tFile = self.TEMPLATES_DIR + "/ldif/GlueSE"
        params = {}
        params["GlueSEUniqueID"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"]
        params["GlueSEName"] = self.configuration["SITE_NAME"] + ":srm_v2"
        params["GlueSESizeTotal"] = round_div(self.stats["summary"]["total-space"],1000000000) + round_div(self.stats["summary"]["nearline-space"],1000000000)
        params["GlueSESizeFree"] = round_div(self.stats["summary"]["free-space"],1000000000)
        params["GlueSETotalOnlineSize"] = round_div(self.stats["summary"]["total-space"],1000000000)
        params["GlueSEUsedOnlineSize"] = round_div(self.stats["summary"]["used-space"],1000000000)
        params["GlueSETotalNearlineSize"] = round_div(self.stats["summary"]["nearline-space"],1000000000)
        params["GlueSiteUniqueID"] = self.configuration["SITE_NAME"]
        params["GlueInformationServiceURL"] = "ldap://" + self.configuration["STORM_BACKEND_HOST"] + ":2170/mds-vo-name=resource,o=grid"
        create_file_from_template(self.GLUE13_STATIC_LDIF_FILE, tFile, params)
        for sa_name in self.stats["sas"]:
            # GlueSA
            sa_data = self.stats["sas"][sa_name]
            params = {}
            params["GlueSALocalID"] = ":".join((sa_name, sa_data["retentionPolicy"], sa_data["accessLatency"]))
            params["GlueSAVOName"] = sa_data["voname"]
            params["GlueSEUniqueID"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"]
            if '*' in sa_data["voname"]:
                params["GlueSAName"] = "Custom space for non-VO users"
            else:
                params["GlueSAName"] = "Reserved space for " + sa_data["voname"] + " VO"
            params["GlueSATotalOnlineSize"] = round_div(sa_data["total-space"],1000000000) # total space in GB
            params["GlueSAUsedOnlineSize"] = round_div(sa_data["used-space"],1000000000) # used space in GB
            params["GlueSAFreeOnlineSize"] = round_div(sa_data["free-space"],1000000000) # free space in GB
            params["GlueSAReservedOnlineSize"] = round_div(sa_data["total-space"],1000000000) # reserved = total in prev bash script for Glue1.3
            params["GlueSATotalNearlineSize"] = round_div(sa_data["availableNearlineSpace"],1000000000) # nearline size in GB
            params["GlueSARetentionPolicy"] = sa_data["retentionPolicy"]
            params["GlueSAStateAvailableSpace"] = round_div(sa_data["available-space"],1000) # available space in KB
            params["GlueSAStateUsedSpace"] = round_div(sa_data["used-space"],1000) # used space in KB
            tFile = self.TEMPLATES_DIR + "/ldif/GlueSA"
            append_file_from_template(self.GLUE13_STATIC_LDIF_FILE, tFile, params)
            if not '*' in sa_data["voname"]:
                # GlueSAVOInfo
                params["GlueVOInfoLocalID"] = ":".join((sa_data["voname"],sa_data["token"]))
                params["GlueVOInfoPath"] = sa_data["stfnRoot"][0]
                params["GlueVOInfoTag"] = sa_data["token"]
                tFile = self.TEMPLATES_DIR + "/ldif/GlueSAVOInfo"
                append_file_from_template(self.GLUE13_STATIC_LDIF_FILE, tFile, params)
        # GlueSEControlProtocol
        params = {}
        params["GlueSEUniqueID"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"]
        params["GlueSEControlProtocolEndpoint"] = self.configuration["STORM_FRONTEND_ENDPOINT"]
        tFile = self.TEMPLATES_DIR + "/ldif/GlueSEControlProtocol"
        append_file_from_template(self.GLUE13_STATIC_LDIF_FILE, tFile, params)
        # GlueSEAccessProtocol for each protocol
        tFile = self.TEMPLATES_DIR + "/ldif/GlueSEAccessProtocol"
        params = {}
        params["GlueSEUniqueID"] = self.configuration["STORM_FRONTEND_PUBLIC_HOST"]
        if self.configuration["STORM_INFO_FILE_SUPPORT"].upper() == "TRUE":
            params["protocol"] = "file"
            params["GlueSEAccessProtocolMaxStreams"] = 1
            append_file_from_template(self.GLUE13_STATIC_LDIF_FILE, tFile, params)
        if self.configuration["STORM_INFO_RFIO_SUPPORT"].upper() == "TRUE":
            params["protocol"] = "rfio"
            params["GlueSEAccessProtocolMaxStreams"] = 1
            append_file_from_template(self.GLUE13_STATIC_LDIF_FILE, tFile, params)
        if self.configuration["STORM_INFO_GRIDFTP_SUPPORT"].upper() == "TRUE":
            params["protocol"] = "gsiftp"
            params["GlueSEAccessProtocolMaxStreams"] = 10
            append_file_from_template(self.GLUE13_STATIC_LDIF_FILE, tFile, params)
        if self.configuration["STORM_INFO_ROOT_SUPPORT"].upper() == "TRUE":
            params["protocol"] = "root"
            params["GlueSEAccessProtocolMaxStreams"] = 1
            append_file_from_template(self.GLUE13_STATIC_LDIF_FILE, tFile, params)
        if self.configuration["STORM_INFO_HTTP_SUPPORT"].upper() == "TRUE":
            params["protocol"] = "http"
            params["GlueSEAccessProtocolMaxStreams"] = 1
            append_file_from_template(self.GLUE13_STATIC_LDIF_FILE, tFile, params)
        if self.configuration["STORM_INFO_HTTPS_SUPPORT"].upper() == "TRUE":
            params["protocol"] = "https"
            params["GlueSEAccessProtocolMaxStreams"] = 1
            append_file_from_template(self.GLUE13_STATIC_LDIF_FILE, tFile, params)
        # set owner
        uid = pwd.getpwnam("ldap").pw_uid
        gid = grp.getgrnam("ldap").gr_gid
        os.chown(self.GLUE13_STATIC_LDIF_FILE, uid, gid)
        os.chmod(self.GLUE13_STATIC_LDIF_FILE, 0644)
        return

    def create_plugin_file(self):

        tFile = self.TEMPLATES_DIR + "/glite-info-dynamic-storm"
        params = {} 
        params["YaimVariablesFile"] = "/etc/storm/backend-server/storm-yaim-variables.conf"
        create_file_from_template(self.GLUE13_INFO_PLUGIN_FILE, tFile, params)
        # set owner
        uid = pwd.getpwnam("ldap").pw_uid
        gid = grp.getgrnam("ldap").gr_gid
        os.chown(self.GLUE13_INFO_PLUGIN_FILE, uid, gid)
        os.chmod(self.GLUE13_INFO_PLUGIN_FILE, 0755)
        return

    def remove_old_cron_file_if_exists(self):

        cFile = "/etc/cron.d/glite-info-dynamic-storm"
        if os.path.isfile(cFile):
            os.remove(cFile)
        return
