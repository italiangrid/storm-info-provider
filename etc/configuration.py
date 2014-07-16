from utils import clear_quotes, clear_newlines

class Configuration:

    mandatories = ["SITE_NAME", "STORM_BACKEND_HOST", "STORM_DEFAULT_ROOT",
        "STORM_FRONTEND_PATH", "STORM_FRONTEND_PORT",
        "STORM_FRONTEND_PUBLIC_HOST", "STORM_BACKEND_REST_SERVICES_PORT", 
        "VOS", "STORM_ENDPOINT_QUALITY_LEVEL", "STORM_ENDPOINT_CAPABILITY"]

    def __init__(self, param):
        if isinstance(param, dict):
            self.configuration = param
        if isinstance(param, basestring):
            self.configuration = self.load_configuration_from_file(param)
        self.configuration_sanity_check()
        return

    def load_configuration_from_file(self, filepath):
        out = {}
        try:
            f = open(filepath, 'r')
            for line in f:
                (key, val) = line.split('=')
                out[key] = clear_quotes(clear_newlines(val.strip()))
        finally:
            f.close()
        return out

    def configuration_sanity_check(self):
        for key in self.mandatories:
            if not key in self.configuration:
                raise ValueError("Configuration error: Missing mandatory \"" + key + "\" variable!")

    def print_configuration(self):
        for key,value in self.configuration.items():
            print str(key) + "=" + str(value) + "\n"

    def get(self, key):
        return self.configuration[key]

    def set(self, key, value):
        self.configuration[key] = value

    def get_enabled_protocols(self):
        enabled = []
        if self.configuration["STORM_INFO_FILE_SUPPORT"].lower() == "true":
            enabled.append("file")
        if self.configuration["STORM_INFO_RFIO_SUPPORT"].lower() == "true":
            enabled.append("rfio")
        if self.configuration["STORM_INFO_GRIDFTP_SUPPORT"].lower() == "true":
            enabled.append("gsiftp")
        if self.configuration["STORM_INFO_ROOT_SUPPORT"].lower() == "true":
            enabled.append("root")
        if self.configuration["STORM_INFO_HTTP_SUPPORT"].lower() == "true":
            enabled.append("http")
        if self.configuration["STORM_INFO_HTTPS_SUPPORT"].lower() == "true":
            enabled.append("https")
        return enabled

    def get_frontend_list(self):
        return self.configuration["STORM_FRONTEND_HOST_LIST"].split(',')

    def has_gridhttps(self):
        return self.configuration['STORM_GRIDHTTPS_ENABLED'].lower() == "true"

    def get_gridhttps_list(self):
        return self.configuration["STORM_GRIDHTTPS_POOL_LIST"].split(',')

    def is_HTTP_endpoint_enabled(self):
        return self.configuration['STORM_GRIDHTTPS_HTTP_ENABLED'].lower() == "true"

    def get_public_srm_endpoint(self):
        return "httpg://" + self.configuration["STORM_FRONTEND_PUBLIC_HOST"] + ":" + self.configuration["STORM_FRONTEND_PORT"] + self.configuration["STORM_FRONTEND_PATH"]

    def is_info_overwrite(self):
        return self.configuration["STORM_INFO_OVERWRITE"].lower() == "true"


