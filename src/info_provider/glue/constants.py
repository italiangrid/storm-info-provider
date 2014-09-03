
# general
INFO_PROVIDER_CONFIG_DIR = "/etc/storm/info-provider"
INFO_PROVIDER_TEMPLATES_DIR = "/etc/storm/info-provider/templates"
INFO_PROVIDER_SCRIPT = "/usr/libexec/storm-info-provider"
INPUT_YAIM_CONFIGURATION = "/etc/storm/info-provider/storm-yaim-variables.conf"

# bdii
BDII_PROVIDER_PATH = "/var/lib/bdii/gip/provider"
BDII_LDIF_PATH = "/var/lib/bdii/gip/ldif"
BDII_PLUGIN_PATH = "/var/lib/bdii/gip/plugin"

# Glue13
GLUE13_BASEDN = "mds-vo-name=resource,o=grid"

GLUE13_INFO_PROVIDER_FILE = BDII_PROVIDER_PATH + "/storm-glue13-provider"
GLUE13_INFO_STATIC_LDIF_FILE = BDII_LDIF_PATH + "/storm-glue13-static.ldif"
GLUE13_INFO_PLUGIN_FILE = BDII_PLUGIN_PATH + "/storm-glue13-plugin"

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
    'xroot': {
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
        },
    'webdav': {
        'version': '1.1',
        'maxstreams': '1'
        }
    }

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