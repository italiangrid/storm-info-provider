import urllib2
import logging
import time

try:
    import json
except ImportError:
    import simplejson as json

class HTTP:

    def __init__(self):
        self.max_attempts = 5
        self.min_delay = 1 # sec
        return

    def getJSON(self, url):
        seconds = self.min_delay
        attempt = 0
        while attempt < self.max_attempts:
            try:
                response = urllib2.urlopen(url)
                return json.load(response)
            except Exception, ex:
                logging.error('%s', ex)
                # try again?
                attempt += 1
                if attempt == self.max_attempts:
                    raise Exception('HTTP.getJSON error: Unable to contact ' + 
                        url + ' after ' + str(attempt) + ' attempts')
                logging.info('Retrying after %s seconds...', seconds)
                time.sleep(seconds)
                seconds *= 2
        raise Exception('HTTP.getJSON error: Unable to contact ' + url)

class SizeT(object):

    def __init__(self, numbytes=0):
        self.numbytes = int(numbytes)
        return

    def add(self, numbytes):
        self.numbytes += int(numbytes)
        return self

    def as_GB(self):
        return int(round(1.0 * self.numbytes/1000000000))

    def as_KB(self):
        return int(round(1.0 * self.numbytes/1000))

    def as_B(self):
        return int(self)

    def __int__(self):
        return self.numbytes

    def __str__(self):
        return str(self.numbytes)

class SpaceInfo(object):

    def __init__(self, configuration):
        self.supported_vos = configuration.get_supported_VOs()
        self.be_endpoint = configuration.get_backend_rest_endpoint()
        self.summary = self._get_empty_space_record()
        self.vos = {}
        for vo in self.supported_vos:
            self.vos[vo] = self._get_empty_space_record()
        self.vfs = {}
        self.build()
        return

    def _get_empty_space_record(self):
        return {
            "total-space": SizeT(),
            "available-space": SizeT(),
            "used-space": SizeT(),
            "free-space": SizeT(),
            "unavailable-space": SizeT(),
            "reserved-space": SizeT(),
            "busy-space": SizeT(),
            "nearline-space": SizeT()
        }

    def _init_space_record_from_response(self, json_data):
        return {
            "total-space": SizeT(json_data["total-space"]),
            "available-space": SizeT(json_data["available-space"]),
            "used-space": SizeT(json_data["used-space"]),
            "free-space": SizeT(json_data["free-space"]),
            "unavailable-space": SizeT(json_data["unavailable-space"]),
            "reserved-space": SizeT(json_data["reserved-space"]),
            "busy-space": SizeT(json_data["busy-space"]),
            "nearline-space": SizeT()
        }

    def _get_VFS_status(self, sa_token):
        url = self.be_endpoint + '/info/status/' + sa_token
        data = HTTP().getJSON(url)
        logging.debug("GET %s = %s", url, data)
        return self._init_space_record_from_response(data["sa-status"])

    def _get_VirtualFSList(self):
        url = self.be_endpoint + '/configuration/1.3/VirtualFSList' 
        data = HTTP().getJSON(url)
        logging.debug("GET %s = %s", url, data)
        return data

    def build(self):
        # get vfs list with general info
        data = self._get_VirtualFSList()
        for vfs_name,vfs_data in data.iteritems():
            # get <vfs_name> space capacity info
            response = self._get_VFS_status(vfs_data["token"])
            response["nearline-space"].add(vfs_data["availableNearlineSpace"])
            # merge vfs general with space info and add them
            self.add_vfs_info(vfs_name, dict(vfs_data.items() + 
                response.items()))
        return self

    def add_vfs_info(self, vfs_name, vfs_data):
        # check duplication
        if vfs_name in self.vfs:
            raise ValueError("SpaceInfo error: Duplicated VFS '" + 
                vfs_name + "'")
        # add vfs info
        self.vfs[vfs_name] = vfs_data
        # add/update vo info
        voname = vfs_data["voname"]
        if voname in self.supported_vos: # excludes voname = .*
            self.vos[voname]["total-space"].add(vfs_data["total-space"])
            self.vos[voname]["available-space"].add(vfs_data["available-space"])
            self.vos[voname]["used-space"].add(vfs_data["used-space"])
            self.vos[voname]["free-space"].add(vfs_data["free-space"])
            self.vos[voname]["unavailable-space"].add(
                vfs_data["unavailable-space"])
            self.vos[voname]["reserved-space"].add(vfs_data["reserved-space"])
            self.vos[voname]["busy-space"].add(vfs_data["busy-space"])
            self.vos[voname]["nearline-space"].add(vfs_data["nearline-space"])
        # update summary
        self.summary["total-space"].add(vfs_data["total-space"])
        self.summary["available-space"].add(vfs_data["available-space"])
        self.summary["used-space"].add(vfs_data["used-space"])
        self.summary["free-space"].add(vfs_data["free-space"])
        self.summary["unavailable-space"].add(vfs_data["unavailable-space"])
        self.summary["reserved-space"].add(vfs_data["reserved-space"])
        self.summary["busy-space"].add(vfs_data["busy-space"])
        self.summary["nearline-space"].add(vfs_data["nearline-space"])
        return

    def get_summary(self):
        return self.summary

    def get_vos(self):
        return self.vos

    def get_vfs(self):
        return self.vfs