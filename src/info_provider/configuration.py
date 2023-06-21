import logging

from info_provider.model.space import ApproachableRule


class Configuration:

    __quality_levels = {
        0: "development",
        1: "testing",
        2: "pre-production",
        3: "production"
    }

    _mandatories = ["SITE_NAME", "STORM_BACKEND_HOST", "STORM_DEFAULT_ROOT",
        "STORM_FRONTEND_PATH", "STORM_FRONTEND_PORT",
        "STORM_FRONTEND_PUBLIC_HOST", "STORM_BACKEND_REST_SERVICES_PORT",
        "VOS", "STORM_ENDPOINT_QUALITY_LEVEL"]

    def __init__(self, filepath):
        logging.debug("Init configuration from file %s ...", filepath)
        self._configuration = self._load_configuration_from_file(filepath)
        self._configuration_sanity_check()
        return

    def _clear_quotes(self, s):
        return s.replace('\"', '').replace("\'", '')

    def _clear_newlines(self, s):
        return s.replace("\n", '')

    def _load_configuration_from_file(self, filepath):
        out = {}
        try:
            f = open(filepath, 'r')
            for line in f:
                (key, val) = line.split('=', 1)
                out[key] = self._clear_quotes(self._clear_newlines(val.strip()))
        finally:
            f.close()
        return out

    def _configuration_sanity_check(self):
        logging.debug("Configuration sanity check ...")
        for key in self._mandatories:
            if not key in self._configuration:
                raise ValueError("Configuration error: Missing mandatory %s variable!" % key)

    def print_configuration(self):
        logging.debug("##############################################")
        logging.debug("##             CONFIGURATION                ##")
        logging.debug("##############################################")
        for key, value in self._configuration.items():
            logging.debug("%s=%s", str(key), str(value))
        logging.debug("##############################################")

    def get(self, key):
        return self._configuration[key]

    def set(self, key, value):
        self._configuration[key] = value

    def get_enabled_access_protocols(self):
        enabled = []
        if self.get("STORM_INFO_FILE_SUPPORT").lower() == "true":
            enabled.append("file")
        if self.get("STORM_INFO_RFIO_SUPPORT").lower() == "true":
            enabled.append("rfio")
        if self.get("STORM_INFO_GRIDFTP_SUPPORT").lower() == "true":
            enabled.append("gsiftp")
        if self.get("STORM_INFO_ROOT_SUPPORT").lower() == "true":
            enabled.append("xroot")
        if self.get("STORM_INFO_HTTP_SUPPORT").lower() == "true":
            enabled.append("http")
        if self.get("STORM_INFO_HTTPS_SUPPORT").lower() == "true":
            enabled.append("https")
        if self.has_webdav():
            enabled.append("webdav")
        return enabled

    def get_backend_rest_endpoint(self):
        host = self.get("STORM_BACKEND_HOST")
        port = self.get("STORM_BACKEND_REST_SERVICES_PORT")
        return 'http://' + host + ':' + str(port)

    def get_frontend_list(self):
        return self.get("STORM_FRONTEND_HOST_LIST").split(',')

    def has_gridhttps(self):
        if 'STORM_GRIDHTTPS_ENABLED' in self._configuration:
            return self.get('STORM_GRIDHTTPS_ENABLED').lower() == "true"
        return False

    def get_gridhttps_list(self):
        return self.get("STORM_GRIDHTTPS_POOL_LIST").split(',')

    def is_HTTP_endpoint_enabled(self):
        return self.get('STORM_GRIDHTTPS_HTTP_ENABLED').lower() == "true"

    def has_webdav(self):
        if 'STORM_WEBDAV_POOL_LIST' in self._configuration:
            if len(self.get_webdav_endpoints()) > 0:
                return True
        return False

    def get_public_srm_endpoint(self):
        host = self.get("STORM_FRONTEND_PUBLIC_HOST")
        port = str(self.get("STORM_FRONTEND_PORT"))
        path = self.get("STORM_FRONTEND_PATH")
        return "httpg://" + host + ":" + port + path

    def get_public_https_endpoint(self):
        host = self.get("STORM_GRIDHTTPS_PUBLIC_HOST")
        port = str(self.get("STORM_GRIDHTTPS_HTTPS_PORT"))
        return "https://" + host + ":" + port + "/"

    def get_public_http_endpoint(self):
        host = self.get("STORM_GRIDHTTPS_PUBLIC_HOST")
        port = str(self.get("STORM_GRIDHTTPS_HTTP_PORT"))
        return "http://" + host + ":" + port + "/"

    def get_webdav_endpoints(self):
        endpoints = filter(None, self.get("STORM_WEBDAV_POOL_LIST").split(','))
        logging.debug("webdav endpoints: " + str(endpoints))
        return endpoints

    def vfs_has_custom_token(self, vfs_name):
        return "STORM_" + vfs_name[:-3] + "_TOKEN" in self._configuration

    def get_supported_VOs(self):
        return self.get("VOS").split(' ')

    def get_used_VOs(self):
        vo_list = []
        for sa in self.get_storage_area_list():
            vos = self.get_sa_vos(sa)
            for vo_name in vos:
                if vo_name == "*":
                    continue
                if not vo_name in vo_list:
                    vo_list.append(vo_name)

        return vo_list

    def get_storage_area_list(self):
        return self.get("STORM_STORAGEAREA_LIST").split(' ')

    def get_sa_short(self, sa):
        return sa.replace(".", "").replace("-", "").replace("_", "").upper()

    def get_sa_vos(self, sa):
        sa_name = self.get_sa_short(sa)
        if "STORM_" + sa_name + "_VONAME" in self._configuration:
            return self.get("STORM_" + sa_name + "_VONAME").split(',')
        if sa in self.get_supported_VOs():
            return [sa]
        return []

    def get_online_size(self, **options):
        if options.get("sa"):
            logging.debug("configuration.get_online_size %s started", options.get("sa"))
        if options.get("vo"):
            logging.debug("configuration.get_online_size %s started", options.get("vo"))
        tot = 0
        for sa in self.get_storage_area_list():
            if options.get("sa") and sa != options.get("sa"):
                continue
            if options.get("vo") and options.get("vo") in self.get_sa_vos(sa):
                continue
            sa_name = self.get_sa_short(sa)
            tot += int(self.get("STORM_" + sa_name + "_ONLINE_SIZE"))
        logging.debug("online_size: %d", tot)
        return tot*1000000000

    def get_nearline_size(self, **options):
        if options.get("sa"):
            logging.debug("configuration.get_nearline_size %s started", options.get("sa"))
        if options.get("vo"):
            logging.debug("configuration.get_nearline_size %s started", options.get("vo"))
        tot = 0
        for sa in self.get_storage_area_list():
            if options.get("sa") and sa != options.get("sa"):
                continue
            if options.get("vo") and options.get("vo") in self.get_sa_vos(sa):
                continue
            sa_name = self.get_sa_short(sa)
            if "STORM_" + sa_name + "_NEARLINE_SIZE" in self._configuration:
                tot += int(self.get("STORM_" + sa_name + "_NEARLINE_SIZE"))
        logging.debug("nearline_size: %d", tot)
        return tot*1000000000

    def get_sa_token(self, sa):
        sa_name = self.get_sa_short(sa)
        if "STORM_" + sa_name + "_TOKEN" in self._configuration:
            return self.get("STORM_" + sa_name + "_TOKEN")
        return sa_name + "_TOKEN"

    def get_sa_root(self, sa):
        sa_name = self.get_sa_short(sa)
        if "STORM_" + sa_name + "_ROOT" in self._configuration:
            return self.get("STORM_" + sa_name + "_ROOT")
        return self.get("STORM_DEFAULT_ROOT")

    def get_sa_class(self, sa):
        sa_name = self.get_sa_short(sa)
        if "STORM_" + sa_name + "_STORAGECLASS" in self._configuration:
            return self.get("STORM_" + sa_name + "_STORAGECLASS")
        return "T0D1"

    def get_sa_accesspoints(self, sa):
        sa_name = self.get_sa_short(sa)
        if "STORM_" + sa_name + "_ACCESSPOINT" in self._configuration:
            return self.get("STORM_" + sa_name + "_ACCESSPOINT").split(" ")
        return [ "/" + sa ]

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
                out.append(ApproachableRule(**{
                    "dn": dn,
                    "vo": vo_name,
                }))
            else:
                out.append(ApproachableRule(**{
                    "dn": "*",
                    "vo": vo_name,
                }))
        if len(out) == 0:
            out.append(ApproachableRule(**{
                "dn": "*",
                "vo": "*",
            }))
        return out

    def get_sitename(self):
        return self.get("SITE_NAME")

    def get_implementation_version(self):
        return self.get("STORM_IMPLEMENTATION_VERSION")

    def get_quality_level(self):
        return self.__quality_levels[int(self.get('STORM_ENDPOINT_QUALITY_LEVEL'))]

    def get_serving_state(self):
        return self.get("STORM_SERVING_STATE")

    def get_backend_hostname(self):
        return self.get("STORM_BACKEND_HOST")

    def get_issuer_ca(self):
        return self.get("ISSUER_CA")
