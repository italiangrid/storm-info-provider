
class SpaceInfo:

    def __init__(self, **data):
        self.summary = data.get("summary") if data.get("summary") else SpaceRecord()
        self.vos = data.get("vo_lists") if data.get("vo_list") else {}
        self.vfs = data.get("vfs_list") if data.get("vfs_list") else {}

    def get_summary(self):
        return self.summary

    def get_vos(self):
        return self.vos

    def get_vfs(self):
        return self.vfs

class SpaceRecord:

    def __init__(self, **data):
        self._init_as_empty()
        # initialize with default value:
        if data.get("total"):
            self.total = int(data.get("total"))
        if data.get("available"):
            self.available = int(data.get("available"))
        else:
            self.available = self.total
        if data.get("used"):
            self.used = int(data.get("used"))
        if data.get("free"):
            self.free = int(data.get("free"))
        else:
            self.free = self.total
        if data.get("unavailable"):
            self.unavailable = int(data.get("unavailable"))
        if data.get("reserved"):
            self.reserved = int(data.get("reserved"))
        if data.get("busy"):
            self.busy = int(data.get("busy"))
        if data.get("near_line"):
            self.nearline = int(data.get("near_line"))

    def _init_as_empty(self):
        self.total = 0
        self.available = 0
        self.used = 0
        self.free = 0
        self.unavailable = 0
        self.reserved = 0
        self.busy = 0
        self.nearline = 0

    def get_total(self):
        return self.total

    def get_available(self):
        return self.available

    def get_used(self):
        return self.used

    def get_free(self):
        return self.free

    def get_unavailable(self):
        return self.unavailable

    def get_reserved(self):
        return self.reserved

    def get_busy(self):
        return self.busy

    def get_nearline(self):
        return self.nearline

    def has_online_capacity(self):
        return self.total > 0

    def has_nearline_capacity(self):
        return self.nearline > 0

    def sum(self, sr2):
        self.total = self.total + int(sr2.get_total())
        self.available = int(self.available) + int(sr2.get_available())
        self.used = int(self.used) + int(sr2.get_used())
        self.free = int(self.free) + int(sr2.get_free())
        self.unavailable = int(self.unavailable) + int(sr2.get_unavailable())
        self.reserved = int(self.reserved) + int(sr2.get_reserved())
        self.busy = int(self.busy) + int(sr2.get_busy())
        self.nearline = int(self.nearline) + int(sr2.get_nearline())

    def __str__(self):
        str_list = []
        str_list.append("total: %d" % self.total)
        str_list.append("available: %d" % self.available)
        str_list.append("used: %d" % self.used)
        str_list.append("free: %d" % self.free)
        str_list.append("unavailable: %d" % self.unavailable)
        str_list.append("reserved: %d" % self.reserved)
        str_list.append("busy: %d" % self.busy)
        str_list.append("near_line: %d" % self.nearline)
        return "[" + ", ".join(str_list) + "]"


class VirtualFileSystemRecord:

    def __init__(self, **data):
        self.name = data.get("name") if data.get("name") else ""
        self.token = data.get("token") if data.get("token") else ""
        self.voname = data.get("vo_name") if data.get("vo_name") else ""
        self.root = data.get("root") if data.get("root") else ""
        self.storageclass = data.get("storage_class") if data.get("storage_class") else ""
        self.stfnroot = data.get("stfn_root") if data.get("stfn_root") else []
        self.retentionpolicy = data.get("retention_policy") if data.get("retention_policy") else ""
        self.accesslatency = data.get("access_latency") if data.get("access_latency") else ""
        self.protocols = data.get("protocols") if data.get("protocols") else []
        self.approachablerules = data.get("approachable_rules") if data.get("approachable_rules") else []
        self.space = data.get("space") if data.get("space") else SpaceRecord()

    def get_name(self):
        return self.name

    def get_token(self):
        return self.token

    def get_voname(self):
        return self.voname

    def get_root(self):
        return self.root

    def get_storageclass(self):
        return self.storageclass

    def get_retentionpolicy(self):
        return self.retentionpolicy

    def get_accesslatency(self):
        return self.accesslatency

    def get_stfnroot(self):
        return self.stfnroot

    def get_protocols(self):
        return self.protocols

    def get_approachablerules(self):
        return self.approachablerules

    def get_space(self):
        return self.space

    def __str__(self):
        str_list = []
        str_list.append("name: %d" % self.name)
        str_list.append("token: %d" % self.token)
        str_list.append("vo_name: %d" % self.root)
        str_list.append("root: %d" % self.root)
        str_list.append("storage_class: %d" % self.storageclass)
        str_list.append("access_latency: %d" % self.accesslatency)
        str_list.append("retention_policy: %d" % self.retentionpolicy)
        str_list.append("access_latency: %d" % self.accesslatency)
        str_list.append("stfn_root: %d" % self.stfnroot)
        str_list.append("protocols: %d" % self.protocols)
        str_list.append("approachable_rules: %d" % self.approachablerules)
        str_list.append("space: %d" % self.space.__str__())
        return "[" + ", ".join(str_list) + "]"