import logging

from tests.utils import get_default_test_configuration,\
    get_default_test_configuration_filepath,\
    get_incomplete_test_configuration_filepath
from info_provider.configuration import Configuration

try:
    import unittest2 as unittest
except ImportError:
    import unittest

logging.getLogger(__name__)

class TestConfiguration(unittest.TestCase):

    def _check_is_test_configuration(self, configuration, filepath):
        logging.debug("Configuration check: verify %s contains values from file %s", configuration, filepath)
        config = {}
        configfile = open(filepath,'r')
        configlist = configfile.readlines()
        for x in configlist:
            if not (x[:1] == '[' or x[:1] == '/'):
                line = x.replace(';','').replace('\n','').replace('\'','').split('=')
                key = line[0]
                value = line[1]
                self.assertEqual(configuration.get(key), value)
                config[key] = value
        self.assertEqual(configuration.get_sitename(), config["SITE_NAME"])
        self.assertEqual(configuration.get_domain(), config["MY_DOMAIN"])
        self.assertEqual(configuration.get_serving_state(), "production")
        self.assertEqual(configuration.get_backend_hostname(), config["STORM_BACKEND_HOST"])
        self.assertEqual(configuration.get_quality_level(), "testing")
        self.assertEqual(configuration.get_implementation_version(), "1.11.13")
        self.assertEqual(configuration.get_storage_area_list(), config["STORM_STORAGEAREA_LIST"].split(' '))
        self.assertEqual(configuration.get_frontend_list(), config["STORM_FRONTEND_HOST_LIST"].split(','))
        logging.debug("Check success")

    def test_load_default_configuration(self):
        configuration = get_default_test_configuration()
        self._check_is_test_configuration(configuration, get_default_test_configuration_filepath())

    def test_load_configuration_from_file(self):
        configuration = get_default_test_configuration()
        configfile = open(get_default_test_configuration_filepath(),'r')
        configlist = configfile.readlines()
        for x in configlist:
            if not (x[:1] == '[' or x[:1] == '/'):
                line = x.replace(';','').replace('\n','').replace('\'','').split('=')
                self.assertEqual(configuration.get(line[0]), line[1])

    def test_missing_mandatory_variable(self):
        with self.assertRaises(ValueError) as cm:
            Configuration(get_incomplete_test_configuration_filepath())
        self.assertEqual(cm.exception.message, "Configuration error: Missing mandatory SITE_NAME variable!")

    def test_print_configuration(self):
        configuration = get_default_test_configuration()
        configuration.print_configuration()

if __name__ == "__main__":
    unittest.main()
