import logging
import json

from info_provider.model.space import SpaceInfo, SpaceRecord, VirtualFileSystemRecord

class SpaceInfoBuilder:

    def __init__(self, configuration):
        self._configuration = configuration

    def build(self):
        return self._load_space_info()

    def _as_JSON(self, obj):
        return json.dumps(obj, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def _load_space_info(self):
        return self._build_from_remote_response()

    def _build_from_remote_response(self):
        logging.debug("Initializing space info from remote storm response ...")
        summary = SpaceRecord(**{
            "total": 0,
            "near_line": 0
            })
        vfs = {}
        vos = {}
        srr = self._configuration.get("SRR_JSON")
        for data in srr["storageservice"]["storageshares"]:
            space = SpaceRecord(**{
                "total": int(data["totalsize"]),
                "used": int(data["usedsize"]),
                "free": int(data["totalsize"]) - int(data["usedsize"]),
                "reserved": 0,
                "busy": 0,
                "near_line": int(data["totalsize"])
                })
            logging.debug("%s", self._as_JSON(space))
            vfs[data["name"]] = VirtualFileSystemRecord(**{
                "name": data["name"],
                "vos": ' '.join(data["vos"]),
                "stfn_root": data["path"][0],
                "retention_policy": "custodial" if "tape" in data["name"] else "replica",
                "access_latency": data["accesslatency"],
                "protocols": ["https", "webdav"],
                "approachable_rules": ["vo:" + vo for vo in data["vos"]],
                "space": space
                })
            logging.debug("%s", self._as_JSON(vfs[data["name"]]))

            # add/update VO space info
            if not "*" in data["vos"]:
                for vo_name in data["vos"]:
                    if not vo_name in vos:
                        vos[vo_name] = SpaceRecord(**{
                            "total": int(data["totalsize"]),
                            "used": int(data["usedsize"]),
                            "free": int(data["totalsize"]) - int(data["usedsize"]),
                            "reserved": 0,
                            "busy": 0,
                            "near_line": int(data["totalsize"])
                            })
                    else:
                        vos[vo_name].sum(space)

            # update summary
            summary.sum(space)

        logging.debug("%s", self._as_JSON(summary))

        return SpaceInfo(**{
            "summary": summary,
            "vo_list": vos,
            "vfs_list": vfs
            })
