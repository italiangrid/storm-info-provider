from info_provider.glue.commons import *

# Glue2

GLUE2_BASEDN = "GLUE2GroupID=resource,o=glue"

GLUE2_INFO_PROVIDER_FILE = BDII_PROVIDER_PATH + "/storm-glue2-provider"
GLUE2_INFO_STATIC_LDIF_FILE = BDII_LDIF_PATH + "/storm-glue2-static.ldif"
GLUE2_INFO_PLUGIN_FILE = BDII_PLUGIN_PATH + "/storm-glue2-plugin"

GLUE2_INFO_SERVICE_CONFIG_FILE_TEMPLATE = INFO_PROVIDER_TEMPLATES_DIR + \
    "/glite-info-glue2-service-storm.conf.template"
GLUE2_INFO_SERVICE_CONFIG_FILE = INFO_PROVIDER_CONFIG_DIR + \
    "/glite-info-glue2-service-storm.conf"
GLUE2_INFO_SERVICE_SRM_CONFIG_FILE_TEMPLATE = INFO_PROVIDER_TEMPLATES_DIR + \
    "/glite-info-glue2-service-storm-endpoint-srm.conf.template"
GLUE2_INFO_SERVICE_SRM_CONFIG_FILE = INFO_PROVIDER_CONFIG_DIR + \
    "/glite-info-glue2-service-storm-endpoint-srm.conf"

GLUE2_ACCESS_PROTOCOLS_VERSIONS = {
    'file': '1.0.0',
    'rfio': '1.0.0',
    'xroot': '1.0.0',
    'http': '1.1.0',
    'https': '1.1.0',
    'gsiftp': '2.0.0',
    'webdav': '1.1'
}
