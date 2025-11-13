import logging

from tests.utils import get_default_test_configuration,\
    get_default_test_configuration_filepath

import unittest

logging.getLogger(__name__)

class TestConfiguration(unittest.TestCase):

    def _check_is_test_configuration(self, configuration, filepath):
        logging.debug("Configuration check: verify %s contains values from file %s", configuration, filepath)
        self.assertEqual(configuration.get_sitename(), "INFN-T1")
        self.assertEqual(configuration.get_serving_state(), "production")
        self.assertEqual(configuration.get_webdav_endpoints(), ["https://xfer-test.cr.cnaf.infn.it:8443"])
        self.assertEqual(configuration.get_quality_level(), "production")
        self.assertEqual(configuration.get_implementation_version(), "1.11.0")
        self.assertEqual(configuration.get_storage_area_list(), ["infotest", "ops", "testgrouptape", "testdatatape", "wlcg", "testmctape", "test", "dteam", "dteam-tape"])
        logging.debug("Check success")

    def test_load_default_configuration(self):
        configuration = get_default_test_configuration()
        self._check_is_test_configuration(configuration, get_default_test_configuration_filepath())

    def test_print_configuration(self):
        configuration = get_default_test_configuration()
        configuration.print_configuration()

if __name__ == "__main__":
    unittest.main()
