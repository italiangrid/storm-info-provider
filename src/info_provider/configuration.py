import logging
import urllib.request
import json
import ssl

from info_provider.model.space import ApproachableRule


class Configuration:
    def __init__(self, **data):
        if data.get("url"):
            logging.debug("Init configuration from %s ...", data.get("url"))
            self._configuration = self._load_configuration_from_url(data.get("url"))
            self._configuration["SRR_URL"] = data.get("url")
        elif data.get("path"):
            logging.debug("Init configuration from %s ...", data.get("path"))
            self._configuration = self._load_configuration_from_file(data.get("path"))
        return

    def _load_configuration_from_url(self, url):
        context = ssl.create_default_context()
        context.load_verify_locations(capath="/etc/grid-security/certificates/")
        with urllib.request.urlopen(url, context=context) as f:
            return self._load_configuration(f)

    def _load_configuration_from_file(self, path):
        with open(path) as f:
            return self._load_configuration(f)

    def _load_configuration(self, readable):
        out = {}
        srr = json.load(readable)
        out["SRR_JSON"] = srr
        out["SITE_NAME"] = srr.get("storageservice").get("name")
        out["STORM_ENDPOINT_QUALITY_LEVEL"] = srr["storageservice"]["storageendpoints"][
            0
        ]["qualitylevel"]
        out["STORM_WEBDAV_POOL_LIST"] = srr["storageservice"]["storageendpoints"][0][
            "endpointurl"
        ]
        out["STORM_IMPLEMENTATION_VERSION"] = srr["storageservice"][
            "implementationversion"
        ]
        out["STORM_STORAGEAREA_LIST"] = " ".join(
            [
                storageshare["name"]
                for storageshare in srr["storageservice"]["storageshares"]
            ]
        )
        out["STORM_SERVING_STATE"] = srr["storageservice"]["qualitylevel"]
        out["VOS"] = []
        for share in srr["storageservice"]["storageshares"]:
            out["VOS"].extend(share["vos"])
        return out

    def print_configuration(self):
        logging.debug("##############################################")
        logging.debug("##             CONFIGURATION                ##")
        logging.debug("##############################################")
        for key, value in list(self._configuration.items()):
            logging.debug("%s=%s", str(key), str(value))
        logging.debug("##############################################")

    def get(self, key):
        return self._configuration[key]

    def set(self, key, value):
        self._configuration[key] = value

    def get_enabled_access_protocols(self):
        return ["https", "webdav"]

    def get_webdav_endpoints(self):
        endpoints = [
            e for e in self.get("STORM_WEBDAV_POOL_LIST").split(",") if e is not None
        ]

        logging.debug("webdav endpoints: " + str(endpoints))
        return endpoints

    def get_supported_VOs(self):
        return self.get("VOS")

    def get_used_VOs(self):
        vo_list = []
        for sa in self.get_storage_area_list():
            vos = self.get_sa_vos(sa)
            for vo_name in vos:
                if vo_name == "*":
                    continue
                if vo_name not in vo_list:
                    vo_list.append(vo_name)

        return vo_list

    def get_storage_area_list(self):
        return self.get("STORM_STORAGEAREA_LIST").split(" ")

    def get_sa_short(self, sa):
        return sa.replace(".", "").replace("-", "").replace("_", "").upper()

    def get_sa_vos(self, sa):
        sa_name = self.get_sa_short(sa)
        if "STORM_" + sa_name + "_VONAME" in self._configuration:
            return self.get("STORM_" + sa_name + "_VONAME").split(",")
        if sa in self.get_supported_VOs():
            return [sa]
        return []

    def get_sa_class(self, sa):
        sa_name = self.get_sa_short(sa)
        if "STORM_" + sa_name + "_STORAGECLASS" in self._configuration:
            return self.get("STORM_" + sa_name + "_STORAGECLASS")
        return "T0D1"

    def get_sa_accesspoints(self, sa):
        sa_name = self.get_sa_short(sa)
        if "STORM_" + sa_name + "_ACCESSPOINT" in self._configuration:
            return self.get("STORM_" + sa_name + "_ACCESSPOINT").split(" ")
        return ["/" + sa]

    def get_sa_retention_policy(self, sa):
        if "T1" in self.get_sa_class(sa):
            return "custodial"
        return "replica"

    def get_sa_access_latency(self, sa):
        if "D0" in self.get_sa_class(sa):
            return "nearline"
        return "online"

    def get_sa_approachable_rules(self, sa):
        # compute dn regex if present
        sa_name = self.get_sa_short(sa)
        dn = []
        if "STORM_" + sa_name + "_DN_C_REGEX" in self._configuration:
            dn.append("/C=" + self.get("STORM_" + sa_name + "_DN_C_REGEX"))
        if "STORM_" + sa_name + "_DN_O_REGEX" in self._configuration:
            dn.append("/O=" + self.get("STORM_" + sa_name + "_DN_O_REGEX"))
        if "STORM_" + sa_name + "_DN_OU_REGEX" in self._configuration:
            dn.append("/OU=" + self.get("STORM_" + sa_name + "_DN_OU_REGEX"))
        if "STORM_" + sa_name + "_DN_L_REGEX" in self._configuration:
            dn.append("/L=" + self.get("STORM_" + sa_name + "_DN_L_REGEX"))
        if "STORM_" + sa_name + "_DN_CN_REGEX" in self._configuration:
            dn.append("/CN=" + self.get("STORM_" + sa_name + "_DN_CN_REGEX"))
        # compute list of ar, one for each supported vo
        out = []
        for vo_name in self.get_sa_vos(sa):
            if len(dn) > 0:
                out.append(
                    ApproachableRule(
                        **{
                            "dn": dn,
                            "vo": vo_name,
                        }
                    )
                )
            else:
                out.append(
                    ApproachableRule(
                        **{
                            "dn": "*",
                            "vo": vo_name,
                        }
                    )
                )
        if len(out) == 0:
            out.append(
                ApproachableRule(
                    **{
                        "dn": "*",
                        "vo": "*",
                    }
                )
            )
        return out

    def get_sitename(self):
        return self.get("SITE_NAME")

    def get_implementation_version(self):
        return self.get("STORM_IMPLEMENTATION_VERSION")

    def get_quality_level(self):
        return self.get("STORM_ENDPOINT_QUALITY_LEVEL")

    def get_serving_state(self):
        return self.get("STORM_SERVING_STATE")
