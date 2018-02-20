import logging

from info_provider.model.space import SpaceInfo, SpaceRecord, VirtualFileSystemRecord


class SpaceInfoBuilder:

    def __init__(self, configuration, gateway):
        self._configuration = configuration
        self._gateway = gateway

    def build(self):
        return self._load_space_info()

    def _load_space_info(self):
        serving_state = self._configuration.get_serving_state()
        if serving_state == "closed":
            logging.info("StoRM serving state is: closed")
            return self._build_from_configuration()
        try:
            return self._build_from_remote_response()
        except Exception, ex:
            logging.error('%s', ex)
            return self._build_from_configuration()

    def _build_from_configuration(self):
        logging.info("Initializing space info from configuration ...")
        # initialize summary space info
        summary = SpaceRecord(**{
                    "total": self._configuration.get_online_size(),
                    "near_line": self._configuration.get_nearline_size()
                    })
        # initialize space info for each VO
        vos = {}
        for vo in self._configuration.get_supported_VOs():
            vos[vo] = SpaceRecord(**{
                    "total": self._configuration.get_online_size(vo=vo),
                    "near_line": self._configuration.get_nearline_size(vo=vo)
                    })
        # initialize space info for each virtual-file-system
        vfs = {}
        for sa in self._configuration.get_storage_area_list():
            name = self._configuration.get_sa_short(sa) + "-FS"
            vfs[name] = VirtualFileSystemRecord(**{
                "name": name,
                "token": self._configuration.get_sa_token(sa),
                "vo_name": self._configuration.get_sa_voname(sa),
                "root": self._configuration.get_sa_root(sa),
                "storage_class": self._configuration.get_sa_class(sa),
                "stfn_root": self._configuration.get_sa_accesspoints(sa),
                "retention_policy": self._configuration.get_sa_retention_policy(sa),
                "access_latency": self._configuration.get_sa_access_latency(sa),
                "protocols": self._configuration.get_enabled_access_protocols(),
                "approachable_rules": self._configuration.get_sa_approachable_rules(sa),
                "space": SpaceRecord(**{
                    "total": self._configuration.get_online_size(sa=sa),
                    "near_line": self._configuration.get_nearline_size(sa=sa)
                    }),
                })
        logging.debug("Summary: %s", summary.__str__())
        logging.debug("VOs: %s", vos.__str__())
        logging.debug("VFS-list: %s", vfs.__str__())
        return SpaceInfo(**{
            "summary": summary,
            "vo_list": vos,
            "vfs_list": vfs
            })

    def _build_from_remote_response(self):
        logging.info("Initializing space info from remote storm response ...")
        response = self._gateway.get_vfs_list_with_status()
        summary = SpaceRecord(**{
            "total": 0,
            "near_line": 0
            })
        vfs = {}
        vos = {}
        for name, data in response.items():

            space = SpaceRecord(**{
                "total": int(data["space"]["total-space"]),
                "available": int(data["space"]["available-space"]),
                "used": int(data["space"]["used-space"]),
                "free": int(data["space"]["free-space"]),
                "unavailable": int(data["space"]["unavailable-space"]),
                "reserved": int(data["space"]["reserved-space"]),
                "busy": int(data["space"]["busy-space"]),
                "near_line": int(data["availableNearlineSpace"])
                })
            vo_name = data["voname"]
            vfs[name] = VirtualFileSystemRecord(**{
                "name": name,
                "token": data["token"],
                "vo_name": vo_name,
                "root": data["root"],
                "storage_class": data["storageclass"],
                "stfn_root": data["stfnRoot"],
                "retention_policy": data["retentionPolicy"],
                "access_latency": data["accessLatency"],
                "protocols": data["protocols"],
                "approachable_rules": data["approachableRules"],
                "space": space
                })

            # add/update VO space info
            if not "*" in vo_name:
                if not vo_name in vos:
                    vos[vo_name] = space
                else:
                    vos[vo_name].sum(space)

            # update summary
            summary.sum(space)

        logging.debug("Summary: %s", summary.__str__())
        logging.debug("VOs: %s", vos.__str__())
        logging.debug("VFS-list: %s", vfs.__str__())
        return SpaceInfo(**{
            "summary": summary,
            "vo_list": vos,
            "vfs_list": vfs
            })
