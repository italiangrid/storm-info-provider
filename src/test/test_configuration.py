from test.utils import get_default_test_configuration, get_default_test_configuration_filepath

try:
    import unittest2 as unittest
except ImportError:
    import unittest

class TestConfiguration(unittest.TestCase):

    def _check_is_test_configuration(self, configuration, filepath):
        config = {}
        configfile = open(filepath,'r')
        configlist = configfile.readlines()
        for x in configlist:
            if not (x[:1] == '[' or x[:1] == '/'):
                line = x.replace(';','').replace('\n','').replace('\'','').split('=')
                self.assertEqual(configuration.get(line[0]), line[1])
                config[line[0]] = line[1]
        self.assertEqual(configuration.get_sitename(), config["SITE_NAME"])
        self.assertEqual(configuration.get_domain(), config["MY_DOMAIN"])
        self.assertEqual(configuration.get_serving_state(), config["STORM_SERVING_STATE"])
        self.assertEqual(configuration.get_backend_hostname(), config["STORM_BACKEND_HOST"])
        self.assertEqual(configuration.get_quality_level(), "testing")
        self.assertEqual(configuration.get_implementation_version(), "1.11.13")
        self.assertEqual(configuration.get_storage_area_list(), config["STORM_STORAGEAREA_LIST"].split(' '))

    def test_load_configuration_from_file(self):
        configuration = get_default_test_configuration()
        configfile = open(get_default_test_configuration_filepath(),'r')
        configlist = configfile.readlines()
        for x in configlist:
            if not (x[:1] == '[' or x[:1] == '/'):
                line = x.replace(';','').replace('\n','').replace('\'','').split('=')
                self.assertEqual(configuration.get(line[0]), line[1])
        