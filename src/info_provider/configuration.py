import string

class Configuration:

    _mandatories = ["SITE_NAME", "STORM_BACKEND_HOST", "STORM_DEFAULT_ROOT",
        "STORM_FRONTEND_PATH", "STORM_FRONTEND_PORT",
        "STORM_FRONTEND_PUBLIC_HOST", "STORM_BACKEND_REST_SERVICES_PORT",
        "VOS", "STORM_ENDPOINT_QUALITY_LEVEL", "STORM_ENDPOINT_CAPABILITY",
        "STORM_GRIDHTTPS_PUBLIC_HOST"]

    def __init__(self, param):
        if isinstance(param, dict):
            self._configuration = param
        if isinstance(param, basestring):
            self._configuration = self.load_configuration_from_file(param)
        self.configuration_sanity_check()
        return

    def clear_quotes(self, s):
        return s.replace('\"','').replace("\'",'')

    def clear_newlines(self, s):
        return s.replace("\n",'')

    def load_configuration_from_file(self, filepath):
        out = {}
        try:
            f = open(filepath, 'r')
            for line in f:
                (key, val) = line.split('=')
                out[key] = self.clear_quotes(self.clear_newlines(val.strip()))
        finally:
            f.close()
        return out

    def configuration_sanity_check(self):
        for key in self._mandatories:
            if not key in self._configuration:
                raise ValueError("Configuration error: Missing mandatory \"" + 
                    key + "\" variable!")

    def print_configuration(self):
        for key,value in self._configuration.items():
            print str(key) + "=" + str(value) + "\n"

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
            enabled.append("root")
        if self.get("STORM_INFO_HTTP_SUPPORT").lower() == "true":
            enabled.append("http")
        if self.get("STORM_INFO_HTTPS_SUPPORT").lower() == "true":
            enabled.append("https")
        return enabled

    def get_backend_rest_endpoint(self):
        host = self.get("STORM_BACKEND_HOST")
        port = self.get("STORM_BACKEND_REST_SERVICES_PORT")
        return 'http://' + host + ':' + str(port)

    def get_frontend_list(self):
        return self.get("STORM_FRONTEND_HOST_LIST").split(',')

    def has_gridhttps(self):
        return self.get('STORM_GRIDHTTPS_ENABLED').lower() == "true"

    def get_gridhttps_list(self):
        return self.get("STORM_GRIDHTTPS_POOL_LIST").split(',')

    def is_HTTP_endpoint_enabled(self):
        return self.get('STORM_GRIDHTTPS_HTTP_ENABLED').lower() == "true"

    def get_public_srm_endpoint(self):
        host = self.get("STORM_FRONTEND_PUBLIC_HOST")
        port = str(self.get("STORM_FRONTEND_PORT"))
        path = self.get("STORM_FRONTEND_PATH")
        return "httpg://" + host + ":" + port + path

    def get_public_https_endpoint(self):
        host = self.get("STORM_GRIDHTTPS_PUBLIC_HOST")
        port = str(self.get("STORM_GRIDHTTPS_HTTPS_PORT"))
        return "https://" + host + ":" + port + "/webdav"

    def get_public_http_endpoint(self):
        host = self.get("STORM_GRIDHTTPS_PUBLIC_HOST")
        port = str(self.get("STORM_GRIDHTTPS_HTTP_PORT"))
        return "http://" + host + ":" + port + "/webdav"

    def is_info_overwrite(self):
        return self.get("STORM_INFO_OVERWRITE").lower() == "true"

    def vfs_has_custom_token(self, vfs_name):
        return "STORM_" + vfs_name[:-3] + "_TOKEN" in self._configuration

    def get_supported_VOs(self):
        return self.get("VOS").split(' ')




