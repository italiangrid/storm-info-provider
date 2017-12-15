import calendar
import json
import logging
import time

class StorageService:

    def __init__(self, **data):
        # required:
        if data.get("name"):
            self.name = data.get("name")
        else:
            raise ValueError("name not found")
        if data.get("version"):
            self.implementationversion = data.get("version")
        else:
            raise ValueError("version not found")
        if data.get("quality_level"):
            self.qualitylevel = data.get("quality_level")
        else:
            raise ValueError("quality_level not found")
        # initialize with default value:
        self.endpoints = data.get("endpoints") if data.get("endpoints") else []
        self.shares = data.get("shares") if data.get("shares") else []
        # automatic values:
        self.implementation = "storm"
        self.capabilities = ['data.management.transfer', 'data.management.storage']
        self.latestupdate = calendar.timegm(time.gmtime())

    def get_name(self):
        return self.name

    def get_implementation(self):
        return self.implementation

    def get_implementation_version(self):
        return self.implementationversion

    def get_quality_level(self):
        return self.qualitylevel

    def get_latest_update(self):
        return self.latestupdate

    def get_capabilities(self):
        return self.capabilities

    def get_endpoints(self):
        return self.endpoints

    def get_shares(self):
        return self.shares

    def add_endpoint(self, endpoint):
        if isinstance(endpoint, StorageEndpoint):
            self.endpoints.append(endpoint)
        else:
            raise ValueError("value is not a StorageEndpoint")

    def add_share(self, share):
        if isinstance(share, StorageShare):
            self.shares.append(share)
        else:
            raise ValueError("value is not a StorageShare")

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class StorageShare:

    def __init__(self, **data):
        # required:
        if data.get("name"):
            self.name = data.get("name")
        else:
            raise ValueError("name not found")
        if data.get("vo_list"):
            self.vos = data.get("vo_list")
        else:
            raise ValueError("vo_list not found")
        if data.get("total_size"):
            self.totalsize = int(data.get("total_size"))
        else:
            raise ValueError("total_size not found")
        if data.get("path"):
            self.path = data.get("path")
        else:
            raise ValueError("path not found")
        # initialize with default value:
        self.accesslatency = data.get("access_latency") if data.get("access_latency") else AccessLatency.online()
        self.retentionpolicy = data.get("retention_policy") if data.get("retention_policy") else RetentionPolicy.NONE
        self.usedsize = data.get("used_size") if data.get("used_size") else 0
        # automatic values:
        self.servingstate = ServingState.OPEN
        self.timestamp = calendar.timegm(time.gmtime())
        self.assignedendpoints = ["all"]

    def get_name(self):
        return self.name

    def get_vos(self):
        return self.vos

    def get_totalsize(self):
        return self.totalsize

    def get_usedsize(self):
        return self.usedsize

    def get_path(self):
        return self.path

    def get_access_latency(self):
        return self.accesslatency

    def get_retention_policy(self):
        return self.retentionpolicy

    def get_serving_state(self):
        return self.servingstate

    def get_timestamp(self):
        return self.timestamp

    def get_assigned_endpoints(self):
        return self.assignedendpoints


class StorageEndpoint:

    def __init__(self, **data):
        # required:
        if data.get("name"):
            self.name = data.get("name")
        else:
            raise ValueError("name not found")
        if data.get("url"):
            self.endpointurl = data.get("url")
        else:
            raise ValueError("url not found")
        if data.get("type"):
            self.interfacetype = data.get("type")
        else:
            raise ValueError("type not found")
        if data.get("version"):
            self.interfaceversion = data.get("version")
        else:
            raise ValueError("version not found")
        if data.get("capabilities"):
            self.capabilities = data.get("capabilities")
        else:
            raise ValueError("capabilities not found")
        if data.get("quality_level"):
            self.qualitylevel = data.get("quality_level")
        else:
            raise ValueError("quality_level not found")
        # automatic values:
        self.assignedshares = ["all"]

    def get_name(self):
        return self.name

    def get_url(self):
        return self.endpointurl

    def get_type(self):
        return self.interfacetype

    def get_version(self):
        return self.interfaceversion

    def get_capabilities(self):
        return self.capabilities

    def get_quality_level(self):
        return self.qualitylevel

    def get_assigned_shares(self):
        return self.assignedshares


class AccessLatency:

    @staticmethod
    def online():
        return "online"

    @staticmethod
    def nearline():
        return "nearline"

    @staticmethod
    def offline():
        return "offline"

    def __init__(self):
        logging.debug("AccessLatency init")

class ServingState:
    OPEN = "open"
    CLOSED = "closed"
    DRAINING = "draining"

class RetentionPolicy:
    NONE = "none"
    INTERMEDIATE = "intermediate"
    REPLICATED = "replicated"