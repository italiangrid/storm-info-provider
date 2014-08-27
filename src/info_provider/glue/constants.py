
# general
INFO_PROVIDER_CONFIG_DIR = "/etc/storm/info-provider"
INFO_PROVIDER_TEMPLATES_DIR = "/etc/storm/info-provider/templates"
STORM_INFO_PROVIDER = "/usr/libexec/storm-info-provider"
CONFIG_FILE = "/etc/storm/backend-server/storm-yaim-variables.conf"
LOG_FILE = "/tmp/storm-info-provider.log"

# bdii
INFO_PROVIDER_PATH = "/var/lib/bdii/gip/provider"
INFO_LDIF_PATH = "/var/lib/bdii/gip/ldif"
INFO_PLUGIN_PATH = "/var/lib/bdii/gip/plugin"

# Glue13
GLUE13_BASEDN = "mds-vo-name=resource,o=grid"

GLUE13_INFO_PROVIDER_FILE = INFO_PROVIDER_PATH + "/storm-glue13-provider"
GLUE13_INFO_STATIC_LDIF_FILE = INFO_LDIF_PATH + "/storm-glue13-static.ldif"
GLUE13_INFO_PLUGIN_FILE = INFO_PLUGIN_PATH + "/storm-glue13-plugin"

GLUE13_INFO_SERVICE_CONFIG_FILE_TEMPLATE = INFO_PROVIDER_TEMPLATES_DIR + \
    "/glite-info-glue13-service-storm.conf.template"
GLUE13_INFO_SERVICE_CONFIG_FILE = INFO_PROVIDER_CONFIG_DIR + \
    "/glite-info-glue13-service-storm.conf"

GLUE13_ACCESS_PROTOCOLS = { 
    'file': {
        'version': '1.0.0',
        'maxstreams': '1'
        },
    'rfio': {
        'version': '1.0.0',
        'maxstreams': '1'
        },
    'gsiftp': {
        'version': '1.0.0',
        'maxstreams': '10'
        }, 
    'root': {
        'version': '1.0.0',
        'maxstreams': '1'
        }, 
    'http': {
        'version': '1.1.0',
        'maxstreams': '1'
        }, 
    'https': {
        'version': '1.1.0',
        'maxstreams': '1'
        }
    }

# Glue2
GLUE2_BASEDN = "GLUE2GroupID=resource,o=glue"

GLUE2_INFO_PROVIDER_FILE = INFO_PROVIDER_PATH + "/storm-glue2-provider"
GLUE2_INFO_STATIC_LDIF_FILE = INFO_LDIF_PATH + "/storm-glue2-static.ldif"
GLUE2_INFO_PLUGIN_FILE = INFO_PLUGIN_PATH + "/storm-glue2-plugin"

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
    'root': '1.0.0',
    'http': '1.1.0',
    'https': '1.1.0',
    'gsiftp': '2.0.0'
}