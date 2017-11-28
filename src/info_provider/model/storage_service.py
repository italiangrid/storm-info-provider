import calendar
import json
import os
import time

class DataStoreType:
    DISK = "disk"
    TAPE = "tape"
    CLOUD = "cloud"

class AccessLatencyType:
    ONLINE = "online"
    NEARLINE = "nearline"
    OFFLINE = "offline"

class RetentionPolicyType:
    NONE = "none"
    INTERMEDIATE = "intermediate"
    REPLICATED = "replicated"

class ExpirationType:
    RELEASE = "release"
    WARN = "warn"
    NEVER = "never"

class ServingStateType:
    OPEN = "open"
    CLOSED = "closed"
    DRAINING = "draining"

class LifetimeType:

    def __init__(self, default, maximum, expiration):
        self.default = default
        self.maximum = maximum
        self.expiration = expiration

class DataStoreType:

    def __init__(self, name, datastoretype, accesslatency, totalsize):
        self.name = name
        self.datastoretype = datastoretype
        self.accesslatency = accesslatency
        self.totalsize = totalsize

class StorageEndpoint:

    def __init__(self, name, endpointurl, interfacetype, interfaceversion, capabilities, qualitylevel, assignedshares):
        self.name = name
        self.endpointurl = endpointurl
        self.interfacetype = interfacetype
        self.interfaceversion = interfaceversion
        self.capabilities = capabilities
        self.qualitylevel = qualitylevel
        self.assignedshares = assignedshares

class SrmStorageEndpoint(StorageEndpoint):

    def __init__(self, name, endpointurl, qualitylevel):
        StorageEndpoint.__init__(self, name, endpointurl, "srm", "2.2", ['data.management.transfer', 'data.management.storage'], qualitylevel, ["all"])

class GsiFtpStorageEndpoint(StorageEndpoint):

    def __init__(self, name, endpointurl, qualitylevel):
        StorageEndpoint.__init__(self, name, endpointurl, "gsiftp", "1.0.0", ['data.management.transfer'], qualitylevel, ["all"])

class WebDavStorageEndpoint(StorageEndpoint):

    def __init__(self, name, endpointurl, qualitylevel):
        StorageEndpoint.__init__(self, name, endpointurl, "dav", "1.1", ['data.management.transfer', 'data.management.storage'], qualitylevel, ["all"])

class StorageShare:

    def __init__(self, name, accesslatency, retentionpolicy, totalsize, usedsize, path, vos):
        self.name = name
        self.servingstate = "open"
        self.accesslatency = accesslatency
        self.retentionpolicy = retentionpolicy
        self.timestamp = calendar.timegm(time.gmtime())
        self.totalsize = totalsize
        self.usedsize = usedsize
        self.path = path
        self.assignedendpoints = ["all"]
        self.vos = vos

class StorageService:

    __quality_levels = {
        0: "development",
        1: "testing",
        2: "pre-production",
        3: "production"
    }

    def __init__(self, configuration, space_info):
        self.name = configuration.get_sitename()
        self.implementation = "storm"
        self.implementationversion = self._get_implementation_version()
        self.qualitylevel = self._get_quality_level(configuration)
        self.capabilities = ['data.management.transfer', 'data.management.storage']
        self.endpoints = []
        self.shares = []
        self._add_endpoint(SrmStorageEndpoint(self.name + "_srm", configuration.get_public_srm_endpoint(), self.qualitylevel))
        for name,data in space_info.vfs.items():
            access_latency = data["accessLatency"].lower()
            retention_policy = data["retentionPolicy"].lower()
            total_size = data["space"]["total-space"]
            used_size = data["space"]["used-space"]
            paths = data["stfnRoot"]
            vos = []
            vos.append(data["voname"])
            sa = StorageShare(name, access_latency, retention_policy, total_size, used_size, paths, vos)
            self.shares.append(sa)
        self.latestupdate = calendar.timegm(time.gmtime())

    def _get_implementation_version(self):
        cmd = "rpm -q --queryformat='%{VERSION}' storm-backend-server"
        return os.popen(cmd).read()

    def _get_quality_level(self, configuration):
        int_value = int(configuration.get('STORM_ENDPOINT_QUALITY_LEVEL'))
        return self.__quality_levels[int_value]

    def _add_endpoint(self, endpoint):
        self.endpoints.append(endpoint)

    def _add_share(self, share):
        self.shares.append(share)

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)