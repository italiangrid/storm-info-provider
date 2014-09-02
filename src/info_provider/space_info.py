import logging

try:
    import json
except ImportError:
    import simplejson as json

from http_utils import HTTP

def space_sum(spacerec1, spacerec2):
    params = {}
    for key in spacerec1:
        params[key] = int(spacerec1[key]) + int(spacerec2[key])
    return params

def get_empty_space_record():
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

def get_base_space_record(o_size, n_size):
    return {
        "total-space": int(o_size),
        "available-space": int(o_size),
        "used-space": 0,
        "free-space": int(o_size),
        "unavailable-space": 0,
        "reserved-space": 0,
        "busy-space": 0,
        "nearline-space": int(n_size)
    }

def get_empty_vfs_record():
    return {
        "name": "",
        "token": "",
        "voname": "",
        "root": "",
        "storageclass": "",
        "stfnRoot": [],
        "retentionPolicy": "",
        "accessLatency": "",
        "protocols": [],
        "approachableRules": [],
        "space": get_empty_space_record()
    }

def has_online_capacity(space_record):
    return int(space_record["total-space"]) > 0

def has_nearline_capacity(space_record):
    return int(space_record["nearline-space"]) > 0


class SpaceInfo(object):

    summary = get_empty_space_record()
    vos = {}
    vfs = {}
    
    def __init__(self):
        return

    def _init_empty(self):
        self.summary = get_empty_space_record()
        self.vos = {}
        self.vfs = {}
        return

    def init_from_configuration(self, c):
        logging.debug("Init space info from configuration")
        # init summary space info
        tot_o_size = c.get_online_size()
        tot_n_size = c.get_nearline_size()
        self.summary = get_base_space_record(tot_o_size, tot_n_size)
        logging.debug("Summary: %s", self.summary)
        # init space info for each vo
        self.vos = {}
        for vo in c.get_supported_VOs():
            vo_o_size = c.get_online_size(vo=vo)
            vo_n_size = c.get_nearline_size(vo=vo)
            self.vos[vo] = get_base_space_record(vo_o_size, vo_n_size)
        logging.debug("VOs: %s", self.vos)
        # init vfs list
        self.vfs = {}
        for sa in c.get_storage_area_list():
            name = c.get_sa_short(sa) + "-FS"
            info = get_empty_vfs_record()
            info["name"] = str(name)
            info["token"] = str(c.get_sa_token(sa))
            info["voname"] = str(c.get_sa_voname(sa))
            info["root"] = str(c.get_sa_root(sa))
            info["storageclass"] = str(c.get_sa_class(sa))
            info["stfnRoot"] = c.get_sa_accesspoints(sa)
            info["retentionPolicy"] = str(c.get_sa_retention_policy(sa))
            info["accessLatency"] = str(c.get_sa_access_latency(sa))
            info["protocols"] = c.get_enabled_access_protocols()
            info["approachableRules"] = c.get_sa_approachable_rules(sa)
            info["space"] = get_base_space_record(
                c.get_online_size(sa=sa),
                c.get_nearline_size(sa=sa))
            self.vfs[name] = info
        logging.debug("VFS-list: %s", self.vfs)
        return

    def _get_vfs_space_info(self, be_endpoint, name, token):
        # get <vfs_name> space info
        url = be_endpoint + '/info/status/' + token
        response = HTTP().getJSON(url)
        logging.debug("GET %s = %s", url, response)
        return response["sa-status"]

    def _get_vfs_list(self, be_endpoint):
        url = be_endpoint + '/configuration/1.3/VirtualFSList'
        data = HTTP().getJSON(url)
        logging.debug("GET %s = %s", url, data)
        return data

    def init_from_remote(self, be_endpoint):
        logging.debug("Init space info from remote endpoint: %s", be_endpoint)
        self._init_empty()
        # get vfs list with general info
        data = self._get_vfs_list(be_endpoint)

        for n,d in data.iteritems():

            # get <vfs_name> space info
            sa = self._get_vfs_space_info(be_endpoint, n, d["token"])

            self.vfs[n] = get_empty_vfs_record()
            self.vfs[n]["name"] = str(n)
            self.vfs[n]["token"] = str(d["token"])
            self.vfs[n]["voname"] = str(d["voname"])
            self.vfs[n]["root"] = str(d["root"])
            self.vfs[n]["storageclass"] = str(d["storageclass"])
            self.vfs[n]["stfnRoot"] = d["stfnRoot"]
            self.vfs[n]["retentionPolicy"] = str(d["retentionPolicy"])
            self.vfs[n]["accessLatency"] = str(d["accessLatency"])
            self.vfs[n]["protocols"] = d["protocols"]
            self.vfs[n]["approachableRules"] = d["approachableRules"]

            info = get_empty_space_record()
            info["total-space"] = int(sa["total-space"])
            info["available-space"] = int(sa["available-space"])
            info["used-space"] = int(sa["used-space"])
            info["free-space"] = int(sa["free-space"])
            info["unavailable-space"] = int(sa["unavailable-space"])
            info["reserved-space"] = int(sa["reserved-space"])
            info["busy-space"] = int(sa["busy-space"])
            info["nearline-space"] = int(d["availableNearlineSpace"]) 

            self.vfs[n]["space"] = info

            # add/update vo info
            VO = d["voname"]
            if not "*" in VO:
                if not VO in self.vos:
                    self.vos[VO] = info
                else:
                    self.vos[VO] = space_sum(self.vos[VO], info)

            # update summary
            self.summary = space_sum(self.summary, info)

        logging.debug("Summary: %s", self.summary)
        logging.debug("VOs: %s", self.vos)
        logging.debug("VFS-list: %s", self.vfs)
        return
