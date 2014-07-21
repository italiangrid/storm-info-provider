import logging 

class SpaceInfo:

    def __init__(self, supported_vos):
        self.supported_vos = supported_vos
        self.summary = self.get_empty_space_record()
        self.vos = {}
        self.vfs = {}
        return

    def get_empty_space_record(self):
        return {
            "total-space": 0,
            "available-space": 0,
            "used-space": 0,
            "free-space": 0,
            "unavailable-space": 0,
            "reserved-space": 0,
            "busy-space": 0,
            "nearline-space": 0
        }

    def add_vfs_info(self, vfs_name, vfs_data):
        # check duplication
        if vfs_name in self.vfs:
            raise ValueError("SpaceInfo error: Duplicated VFS '" + vfs_name + "'")
        # add vfs info
        self.vfs[vfs_name] = vfs_data
        # add/update vo info
        voname = vfs_data["voname"]
        if voname in self.supported_vos: # excludes voname = .*
            if not (voname in self.vos): # adds VO to VOS list and inits values to 0
                self.vos[voname] = self.get_empty_space_record()
            self.vos[voname]["total-space"] += vfs_data["total-space"]
            self.vos[voname]["available-space"] += vfs_data["available-space"]
            self.vos[voname]["used-space"] += vfs_data["used-space"]
            self.vos[voname]["free-space"] += vfs_data["free-space"]
            self.vos[voname]["unavailable-space"] += vfs_data["unavailable-space"]
            self.vos[voname]["reserved-space"] += vfs_data["reserved-space"]
            self.vos[voname]["busy-space"] += vfs_data["busy-space"]
            self.vos[voname]["nearline-space"] += vfs_data["availableNearlineSpace"]
        # update summary
        self.summary["total-space"] += vfs_data["total-space"]
        self.summary["available-space"] += vfs_data["available-space"]
        self.summary["used-space"] += vfs_data["used-space"]
        self.summary["free-space"] += vfs_data["free-space"]
        self.summary["unavailable-space"] += vfs_data["unavailable-space"]
        self.summary["reserved-space"] += vfs_data["reserved-space"]
        self.summary["busy-space"] += vfs_data["busy-space"]
        self.summary["nearline-space"] += vfs_data["availableNearlineSpace"]
        return

    def get_summary(self):
        return self.summary

    def get_vos(self):
        return self.vos

    def get_vfs(self):
        return self.vfs

    def get_managed_vos(self):
        vos = []
        for vfs_name,vfs_data in self.vfs.items():
            if ".*" not in vfs_data["voname"]:
                vos.append(vfs_data["voname"])
        return vos