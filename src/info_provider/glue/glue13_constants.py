from info_provider.glue.commons import BDII_PROVIDER_PATH, BDII_LDIF_PATH, \
    BDII_PLUGIN_PATH, INFO_PROVIDER_TEMPLATES_DIR, INFO_PROVIDER_CONFIG_DIR


# Glue 13
GLUE13_BASEDN = "mds-vo-name=resource,o=grid"

GLUE13_INFO_PROVIDER_FILE = BDII_PROVIDER_PATH + "/storm-glue13-provider"
GLUE13_INFO_STATIC_LDIF_FILE = BDII_LDIF_PATH + "/storm-glue13-static.ldif"
GLUE13_INFO_PLUGIN_FILE = BDII_PLUGIN_PATH + "/storm-glue13-plugin"

GLUE13_INFO_SERVICE_CONFIG_FILE_TEMPLATE = INFO_PROVIDER_TEMPLATES_DIR + "/glite-info-glue13-service-storm.conf.template"
GLUE13_INFO_SERVICE_CONFIG_FILE = INFO_PROVIDER_CONFIG_DIR + "/glite-info-glue13-service-storm.conf"

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