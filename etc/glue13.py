import logging
import stat
import pwd
import grp
import os
import re
import time
import tempfile
import shutil
from sets import Set
from glueutils import *
from utils import *

class Glue13(Glue):

    FROM_BYTES_TO_GB = 1000000000
    FROM_BYTES_TO_KB = 1000

    GLUE13_INFO_SERVICE = GlueConstants.INFO_SERVICE_SCRIPT + "/glite-info-service"
    GLUE13_SERVICE_FILE = GlueConstants.INFO_PROVIDER_PATH + "/service-srm-storm-v2"
    GLUE13_SERVICE_CONFIG_FILE = GlueConstants.INFO_SERVICE_CONFIG + "/glite-info-service-srm-storm-v2.conf"
    GLUE13_STATIC_LDIF_FILE = GlueConstants.INFO_LDIF_PATH + "/static-file-storm.ldif"
    GLUE13_INFO_PLUGIN_FILE = GlueConstants.INFO_PLUGIN_PATH + "/glite-info-dynamic-storm"

    def __init__(self):
        self.creation_time = time.strftime('%Y-%m-%dT%T')
        self.baseDN = []
        self.baseDN = self.baseDN + ["mds-vo-name=resource"]
        self.baseDN = self.baseDN + ["o=grid"]
        self.access_protocols_streams = { 
            'file': '1',
            'rfio': '1', 
            'gsiftp': '10', 
            'root': '1', 
            'http': '1', 
            'https': '1'
        }
        return

    def init(self, configuration, stats):
        # GLUE13_SERVICE_FILE
        logging.debug("Creating %s ...", self.GLUE13_SERVICE_FILE)
        self.create_service_file(configuration)
        logging.info("Successfully created %s !", self.GLUE13_SERVICE_FILE)
        # GLUE13_SERVICE_CONFIG_FILE
        logging.debug("Creating %s ...", self.GLUE13_SERVICE_CONFIG_FILE)
        self.create_service_config_file(configuration, stats)
        logging.info("Successfully created %s !", self.GLUE13_SERVICE_CONFIG_FILE)
        # GLUE13_STATIC_LDIF_FILE
        logging.debug("Creating %s ...", self.GLUE13_STATIC_LDIF_FILE)
        self.create_static_ldif_file(configuration, stats)
        logging.info("Successfully created %s !", self.GLUE13_STATIC_LDIF_FILE)
        # GLUE13_PLUGIN_FILE
        logging.debug("Creating %s ...", self.GLUE13_INFO_PLUGIN_FILE)
        self.create_plugin_file()
        logging.info("Successfully created %s !", self.GLUE13_INFO_PLUGIN_FILE)
        # remove old cron file
        self.remove_old_cron_file_if_exists()
        return

    def update(self, configuration, stats):
        # generates the updater node list
        node_list = self.get_update_nodes(configuration, stats)
        # print LDIF
        GlueUtils.print_update_ldif(node_list)
        return

    def create_service_file(self, configuration):
        params = []
        params.append(configuration['SITE_NAME'])
        params.append("httpg://" + configuration["STORM_FRONTEND_PUBLIC_HOST"] + ":" + configuration["STORM_FRONTEND_PORT"] + configuration["STORM_FRONTEND_PATH"])        
        return super(Glue13, self).create_service_file(self.GLUE13_SERVICE_FILE, self.GLUE13_INFO_SERVICE, self.GLUE13_SERVICE_CONFIG_FILE, params)

    def create_service_config_file(self, configuration, stats):
        content = self.get_service_configuration(configuration, self.get_vos(stats["sas"]))
        return super(Glue13, self).create_service_config_file(self.GLUE13_SERVICE_CONFIG_FILE, content)

    def create_plugin_file(self):
        params = ["/etc/storm/backend-server/storm-yaim-variables.conf"]
        info_service = "/usr/libexec/storm-dynamic-info-provider/glite-info-dynamic-storm"
        return super(Glue13, self).create_plugin_file(self.GLUE13_INFO_PLUGIN_FILE, info_service, params)

    def create_static_ldif_file(self, configuration, stats):
        # list of (dn, entries)
        node_list = []
        # common variables
        GlueSiteUniqueID = configuration["SITE_NAME"]
        GlueSEUniqueID = configuration["STORM_FRONTEND_PUBLIC_HOST"]

        # GlueSE
        (dn, entry) = self.get_GlueSE({
            'GlueSEUniqueID': GlueSEUniqueID,
            'GlueSEName': configuration["SITE_NAME"] + ":srm_v2",
            'GlueSESizeTotal': round_div(stats["summary"]["total-space"],self.FROM_BYTES_TO_GB) + round_div(stats["summary"]["nearline-space"],self.FROM_BYTES_TO_GB),
            'GlueSESizeFree': round_div(stats["summary"]["free-space"],self.FROM_BYTES_TO_GB),
            'GlueSETotalOnlineSize': round_div(stats["summary"]["total-space"],self.FROM_BYTES_TO_GB),
            'GlueSEUsedOnlineSize': round_div(stats["summary"]["used-space"],self.FROM_BYTES_TO_GB),
            'GlueSETotalNearlineSize': round_div(stats["summary"]["nearline-space"],self.FROM_BYTES_TO_GB),
            'GlueSiteUniqueID': configuration["SITE_NAME"],
            'GlueInformationServiceURL': "ldap://" + configuration["STORM_BACKEND_HOST"] + ":2170/mds-vo-name=resource,o=grid"
        })
        node_list.append({ "dn": dn, "entries": entry })

        for sa_name in stats["sas"]:
            # GlueSA
            sa_data = stats["sas"][sa_name]
            sa_params = {
                'GlueSALocalID': ":".join((sa_name, sa_data["retentionPolicy"], sa_data["accessLatency"])),
                'GlueSAVOName': sa_data["voname"],
                'GlueSEUniqueID': GlueSEUniqueID,
                'GlueSATotalOnlineSize': round_div(sa_data["total-space"],self.FROM_BYTES_TO_GB), # total space in GB
                'GlueSAUsedOnlineSize': round_div(sa_data["used-space"],self.FROM_BYTES_TO_GB), # used space in GB
                'GlueSAFreeOnlineSize': round_div(sa_data["free-space"],self.FROM_BYTES_TO_GB), # free space in GB
                'GlueSAReservedOnlineSize': round_div(sa_data["total-space"],self.FROM_BYTES_TO_GB), # reserved = total in prev bash script for Glue1.3
                'GlueSATotalNearlineSize': round_div(sa_data["availableNearlineSpace"],self.FROM_BYTES_TO_GB), # nearline size in GB
                'GlueSARetentionPolicy': sa_data["retentionPolicy"],
                'GlueSAStateAvailableSpace': round_div(sa_data["available-space"],self.FROM_BYTES_TO_KB), # available space in KB
                'GlueSAStateUsedSpace': round_div(sa_data["used-space"],self.FROM_BYTES_TO_KB) # used space in KB
            }
            if self.is_VO(sa_data["voname"]):
                sa_params['GlueSAName'] = "Reserved space for " + sa_data["voname"] + " VO"
            else:
                sa_params['GlueSAName'] = "Custom space for non-VO users"
                
            (dn, entry) = self.get_GlueSALocal(sa_params)
            node_list.append({ "dn": dn, "entries": entry })

            if self.is_VO(sa_data["voname"]):
                # GlueSAVOInfo
                sa_params["GlueVOInfoLocalID"] = ":".join((sa_data["voname"],sa_data["token"]))
                sa_params["GlueVOInfoPath"] = sa_data["stfnRoot"][0]
                sa_params["GlueVOInfoTag"] = sa_data["token"]
                (dn, entry) = self.get_GlueSAVOInfo(sa_params)
                node_list.append({ "dn": dn, "entries": entry })

        # GlueSEControlProtocol
        (dn, entry) = self.get_GlueSEControlProtocol({
            'GlueSEUniqueID': configuration["STORM_FRONTEND_PUBLIC_HOST"],
            'GlueSEControlProtocolEndpoint': "httpg://" + configuration["STORM_FRONTEND_PUBLIC_HOST"] + ":" + configuration["STORM_FRONTEND_PORT"] + configuration["STORM_FRONTEND_PATH"]
        })
        node_list.append({ "dn": dn, "entries": entry })
        # GlueSEAccessProtocol for each protocol
        enabled_prot = self.get_enabled_protocols(configuration)
        for protocol, maxstreams in enabled_prot.items():
            (dn, entry) = self.get_GlueSEAccessProtocol({
                'GlueSEUniqueID': GlueSEUniqueID,
                'GlueSEAccessProtocol': protocol,
                'GlueSEAccessProtocolMaxStreams': maxstreams
            })
            node_list.append({ "dn": dn, "entries": entry })

        # remove old backup files
        self.delete_backup_files()
        # create LDIF file
        return super(Glue13, self).create_static_ldif_file(self.GLUE13_STATIC_LDIF_FILE, node_list, configuration["STORM_INFO_OVERWRITE"].lower())

    def get_update_nodes(self, configuration, stats):
        # node list
        node_list = []
        # commons
        GlueSiteUniqueID = configuration["SITE_NAME"]
        GlueSEUniqueID = configuration["STORM_FRONTEND_PUBLIC_HOST"]

        # GlueSE
        (dn, entry) = self.get_GlueSE_update({
            'GlueSEUniqueID': GlueSEUniqueID,
            'GlueSESizeTotal': round_div(stats["summary"]["total-space"],self.FROM_BYTES_TO_GB) + round_div(stats["summary"]["nearline-space"],self.FROM_BYTES_TO_GB),
            'GlueSESizeFree': round_div(stats["summary"]["free-space"],self.FROM_BYTES_TO_GB),
            'GlueSETotalOnlineSize': round_div(stats["summary"]["total-space"],self.FROM_BYTES_TO_GB),
            'GlueSEUsedOnlineSize': round_div(stats["summary"]["used-space"],self.FROM_BYTES_TO_GB),
            'GlueSETotalNearlineSize': round_div(stats["summary"]["nearline-space"],self.FROM_BYTES_TO_GB)
        })
        node_list.append({ "dn": dn, "entries": entry })

        for sa_name in stats["sas"]:
            # GlueSA
            sa_data = stats["sas"][sa_name]
            (dn, entry) = self.get_GlueSALocal_update({
                'GlueSALocalID': ":".join((sa_name, sa_data["retentionPolicy"], sa_data["accessLatency"])),
                'GlueSEUniqueID': GlueSEUniqueID,
                'GlueSATotalOnlineSize': round_div(sa_data["total-space"],self.FROM_BYTES_TO_GB), # total space in GB
                'GlueSAUsedOnlineSize': round_div(sa_data["used-space"],self.FROM_BYTES_TO_GB), # used space in GB
                'GlueSAFreeOnlineSize': round_div(sa_data["free-space"],self.FROM_BYTES_TO_GB), # free space in GB
                'GlueSAReservedOnlineSize': round_div(sa_data["total-space"],self.FROM_BYTES_TO_GB), # reserved = total in prev bash script for Glue1.3
                'GlueSATotalNearlineSize': round_div(sa_data["availableNearlineSpace"],self.FROM_BYTES_TO_GB), # nearline size in GB
                'GlueSAStateAvailableSpace': round_div(sa_data["available-space"],self.FROM_BYTES_TO_KB), # available space in KB
                'GlueSAStateUsedSpace': round_div(sa_data["used-space"],self.FROM_BYTES_TO_KB) # used space in KB
            })
            node_list.append({ "dn": dn, "entries": entry })

        return node_list

    def delete_backup_files(self):
        directory = os.path.dirname(self.GLUE13_STATIC_LDIF_FILE)
        removed_list = delete_files(directory, r'static-file-storm\.ldif\.bkp_.*')
        logging.debug("Removed backup files: [%s]", removed_list)
        return        

    def remove_old_cron_file_if_exists(self):
        cFile = "/etc/cron.d/glite-info-dynamic-storm"
        if os.path.isfile(cFile):
            os.remove(cFile)
        return

    def get_vos(self, sas):
        vos = Set()
        for sa_name in sas:
            if ".*" not in sas[sa_name]["voname"]:
                vos.add(sas[sa_name]["voname"])
        return vos

    def get_service_configuration(self, configuration, vos):
        GLITE_INFO_SERVICE_VERSION = "2.2.0"
        GLITE_INFO_SERVICE_ENDPOINT = "httpg://" + configuration["STORM_FRONTEND_PUBLIC_HOST"] + ":" + configuration["STORM_FRONTEND_PORT"] + configuration["STORM_FRONTEND_PATH"]
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
            "get_data": "echo",
            "get_services": "echo",
            "get_status": STATUS_CMD,
            "get_owner": OWNER,
            "get_acbr": ACBR
        }
        return content

    def get_enabled_protocols(self, configuration):
        enabled = {}
        if configuration["STORM_INFO_FILE_SUPPORT"].lower() == "true":
            enabled["file"] = self.access_protocols_streams["file"]
        if configuration["STORM_INFO_RFIO_SUPPORT"].lower() == "true":
            enabled["rfio"] = self.access_protocols_streams["rfio"]
        if configuration["STORM_INFO_GRIDFTP_SUPPORT"].lower() == "true":
            enabled["gsiftp"] = self.access_protocols_streams["gsiftp"]
        if configuration["STORM_INFO_ROOT_SUPPORT"].lower() == "true":
            enabled["root"] = self.access_protocols_streams["root"]
        if configuration["STORM_INFO_HTTP_SUPPORT"].lower() == "true":
            enabled["http"] = self.access_protocols_streams["http"]
        if configuration["STORM_INFO_HTTPS_SUPPORT"].lower() == "true":
            enabled["https"] = self.access_protocols_streams["https"]
        return enabled

    def is_VO(self, VO):
        return not '*' in VO

    def check_required_params(self, input_dict, mandatory_list):
        for par_name in mandatory_list:
            if not par_name in input_dict:
                raise ValueError("Missing " + par_name + " parameter!")

    def get_GlueSALocal(self, params): # returns (dn, entry) or ValueError exception
        mandatories = ['GlueSALocalID', 'GlueSEUniqueID', 'GlueSAName', 
            'GlueSATotalOnlineSize', 'GlueSAUsedOnlineSize', 
            'GlueSAFreeOnlineSize', 'GlueSAReservedOnlineSize', 
            'GlueSATotalOnlineSize', 'GlueSATotalNearlineSize', 
            'GlueSATotalNearlineSize', 'GlueSARetentionPolicy', 
            'GlueSAStateAvailableSpace', 'GlueSAStateUsedSpace', 
            'GlueSAVOName']
        self.check_required_params(params, mandatories)
        dn = "GlueSALocalID=" + params['GlueSALocalID'] + ",GlueSEUniqueID=" + params['GlueSEUniqueID'] + ",mds-vo-name=resource,o=grid"
        entry = {
            'objectClass': ['GlueSATop', 'GlueSA', 'GlueSAPolicy', 'GlueSAState', 
                'GlueSAAccessControlBase', 'GlueKey', 'GlueSchemaVersion'],
            'GlueSALocalID': [params['GlueSALocalID']],
            'GlueSAName': [params['GlueSAName']],
            'GlueSATotalOnlineSize': [str(params['GlueSATotalOnlineSize'])],
            'GlueSAUsedOnlineSize': [str(params['GlueSAUsedOnlineSize'])],
            'GlueSAFreeOnlineSize': [str(params['GlueSAFreeOnlineSize'])],
            'GlueSAReservedOnlineSize': [str(params['GlueSAReservedOnlineSize'])],
            'GlueSACapability': ["InstalledOnlineCapacity=" + str(params['GlueSATotalOnlineSize']), 
                "InstalledNearlineCapacity=" + str(params['GlueSATotalNearlineSize'])],
            'GlueSATotalNearlineSize': [str(params['GlueSATotalNearlineSize'])],
            'GlueSAUsedNearlineSize': ['0'],
            'GlueSAFreeNearlineSize': ['0'],
            'GlueSAReservedNearlineSize': ['0'],
            'GlueSARetentionPolicy': [params['GlueSARetentionPolicy']],
            'GlueSAAccessLatency': ['online'],
            'GlueSAExpirationMode': ['neverExpire'],
            'GlueSAPolicyFileLifeTime': ['permanent'],
            'GlueSAType': ['permanent'],
            'GlueSAStateAvailableSpace': [str(params['GlueSAStateAvailableSpace'])],
            'GlueSAStateUsedSpace': [str(params['GlueSAStateUsedSpace'])],
            'GlueSAAccessControlBaseRule': ["VO:" + params['GlueSAVOName']],
            'GlueChunkKey': ["GlueSEUniqueID=" + params['GlueSEUniqueID']],
            'GlueSchemaVersionMajor': ['1'],
            'GlueSchemaVersionMinor': ['3']
        }
        return (dn, entry)

    def get_GlueSALocal_update(self, params):
        mandatories = ['GlueSALocalID', 'GlueSEUniqueID', 
            'GlueSATotalOnlineSize', 'GlueSAUsedOnlineSize', 
            'GlueSAFreeOnlineSize', 'GlueSAReservedOnlineSize', 
            'GlueSATotalOnlineSize', 'GlueSATotalNearlineSize', 
            'GlueSATotalNearlineSize', 'GlueSAStateAvailableSpace', 
            'GlueSAStateUsedSpace']
        self.check_required_params(params, mandatories)
        dn = "GlueSALocalID=" + params['GlueSALocalID'] + ",GlueSEUniqueID=" + params['GlueSEUniqueID'] + ",mds-vo-name=resource,o=grid"
        entry = {
            'GlueSATotalOnlineSize': [str(params['GlueSATotalOnlineSize'])],
            'GlueSAUsedOnlineSize': [str(params['GlueSAUsedOnlineSize'])],
            'GlueSAFreeOnlineSize': [str(params['GlueSAFreeOnlineSize'])],
            'GlueSAReservedOnlineSize': [str(params['GlueSAReservedOnlineSize'])],
            'GlueSATotalNearlineSize': [str(params['GlueSATotalNearlineSize'])],
            'GlueSAUsedNearlineSize': ['0'],
            'GlueSAFreeNearlineSize': ['0'],
            'GlueSAReservedNearlineSize': ['0'],
            'GlueSAStateAvailableSpace': [str(params['GlueSAStateAvailableSpace'])],
            'GlueSAStateUsedSpace': [str(params['GlueSAStateUsedSpace'])]
        }
        return (dn, entry)

    def get_GlueSAVOInfo(self, params):
        mandatories = ['GlueVOInfoLocalID', 'GlueSALocalID', 'GlueSEUniqueID', 
            'GlueVOInfoPath', 'GlueVOInfoTag', 'GlueSAVOName']
        self.check_required_params(params, mandatories)
        dn = "GlueVOInfoLocalID=" + params['GlueVOInfoLocalID'] + ",GlueSALocalID=" + params['GlueSALocalID'] + "GlueSEUniqueID=" + params['GlueSEUniqueID'] + ",mds-vo-name=resource,o=grid"
        entry = {
            'objectClass': ['GlueSATop', 'GlueVOInfo', 'GlueKey', 'GlueSchemaVersion' ],
            'GlueVOInfoLocalID': [params['GlueVOInfoLocalID']],
            'GlueVOInfoPath': [params['GlueVOInfoPath']],
            'GlueVOInfoTag': [params['GlueVOInfoTag']],
            'GlueVOInfoAccessControlBaseRule': ["VO:" + params['GlueSAVOName']],
            'GlueChunkKey': ["GlueSALocalID=" + params['GlueSALocalID'], 
                "GlueSEUniqueID=" + params['GlueSEUniqueID']],
            'GlueSchemaVersionMajor': ["1"],
            'GlueSchemaVersionMinor': ["3"]
        }
        return (dn, entry)

    def get_GlueSE(self, params):
        mandatories = ['GlueSEUniqueID', 'GlueSEName', 'GlueSESizeTotal',
            'GlueSESizeFree', 'GlueSETotalOnlineSize', 'GlueSEUsedOnlineSize',
            'GlueSETotalNearlineSize', 'GlueInformationServiceURL', 
            'GlueSiteUniqueID']
        self.check_required_params(params, mandatories)
        dn = "GlueSEUniqueID=" + params['GlueSEUniqueID'] + ",mds-vo-name=resource,o=grid"
        entry = {
            'objectClass': ['GlueSETop', 'GlueSE', 'GlueInformationService', 
                'GlueKey', 'GlueSchemaVersion'],
            'GlueSEUniqueID': [params['GlueSEUniqueID']],
            'GlueSEName': [params['GlueSEName']],
            'GlueSEArchitecture': ['multidisk'],
            'GlueSEStatus': ['Production'],
            'GlueSEImplementationName': ['StoRM'],
            'GlueSEImplementationVersion': ["`rpm -q --queryformat='%{VERSION}' storm-backend-server`"],
            'GlueSESizeTotal': [str(params['GlueSESizeTotal'])],
            'GlueSESizeFree': [str(params['GlueSESizeFree'])],
            'GlueSETotalOnlineSize': [str(params['GlueSETotalOnlineSize'])],
            'GlueSEUsedOnlineSize': [str(params['GlueSEUsedOnlineSize'])],
            'GlueSETotalNearlineSize': [str(params['GlueSETotalNearlineSize'])],
            'GlueSEUsedNearlineSize': ["0"],
            'GlueInformationServiceURL': [params['GlueInformationServiceURL']],
            'GlueForeignKey': [ "GlueSiteUniqueID=" + params['GlueSiteUniqueID']],
            'GlueSchemaVersionMajor': ["1"],
            'GlueSchemaVersionMinor': ["3"]
        }
        return (dn, entry)

    def get_GlueSE_update(self, params):
        mandatories = ['GlueSEUniqueID', 'GlueSESizeTotal', 'GlueSESizeFree', 
            'GlueSETotalOnlineSize', 'GlueSEUsedOnlineSize',
            'GlueSETotalNearlineSize']
        self.check_required_params(params, mandatories)
        dn = "GlueSEUniqueID=" + params['GlueSEUniqueID'] + ",mds-vo-name=resource,o=grid"
        entry = {
            'GlueSESizeTotal': [str(params['GlueSESizeTotal'])],
            'GlueSESizeFree': [str(params['GlueSESizeFree'])],
            'GlueSETotalOnlineSize': [str(params['GlueSETotalOnlineSize'])],
            'GlueSEUsedOnlineSize': [str(params['GlueSEUsedOnlineSize'])],
            'GlueSETotalNearlineSize': [str(params['GlueSETotalNearlineSize'])],
            'GlueSEUsedNearlineSize': ["0"]
        }
        return (dn, entry)

    def get_GlueSEAccessProtocol(self, params):
        mandatories = ['GlueSEAccessProtocol', 'GlueSEUniqueID', 
            'GlueSEAccessProtocolMaxStreams']
        self.check_required_params(params, mandatories)
        dn = "GlueSEAccessProtocolLocalID=" + params['GlueSEAccessProtocol'] + ",GlueSEUniqueID=" + params['GlueSEUniqueID'] + ",mds-vo-name=resource,o=grid"
        entry = {
            'objectClass': ['GlueSETop', 'GlueSEAccessProtocol', 'GlueKey', 
                'GlueSchemaVersion'],
            'GlueSEAccessProtocolType': [params['GlueSEAccessProtocol']],
            'GlueSEAccessProtocolLocalID': [params['GlueSEAccessProtocol']],
            'GlueSEAccessProtocolVersion': ["1.0.0"],
            'GlueSEAccessProtocolSupportedSecurity': ['GSI'],
            'GlueSEAccessProtocolMaxStreams': [params['GlueSEAccessProtocolMaxStreams']],
            'GlueChunkKey': ["GlueSEUniqueID=" + params['GlueSEUniqueID']],
            'GlueSchemaVersionMajor': ["1"],
            'GlueSchemaVersionMinor': ["3"]
        }
        return (dn, entry)

    def get_GlueSEControlProtocol(self, params):
        mandatories = ['GlueSEUniqueID', 'GlueSEControlProtocolEndpoint']
        self.check_required_params(params, mandatories)
        dn = "GlueSEControlProtocolLocalID=srm_v2.2,GlueSEUniqueID=" + params['GlueSEUniqueID'] + ",mds-vo-name=resource,o=grid"
        entry = {
            'objectClass': ['GlueSETop', 'GlueSEControlProtocol', 'GlueKey', 
                'GlueSchemaVersion'],
            'GlueSEControlProtocolType': ['SRM'],
            'GlueSEControlProtocolLocalID': ['srm_v2.2'],
            'GlueSEControlProtocolVersion': ['2.2.0'],
            'GlueSEControlProtocolEndpoint': [params['GlueSEControlProtocolEndpoint']],
            'GlueChunkKey': ["GlueSEUniqueID=" + params['GlueSEUniqueID']],
            'GlueSchemaVersionMajor': ["1"],
            'GlueSchemaVersionMinor': ["3"]
        }
        return (dn, entry)
