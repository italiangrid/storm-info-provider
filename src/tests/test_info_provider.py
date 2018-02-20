from mock.mock import patch

from info_provider.storm_info_provider import StormInfoProvider
from tests.utils import get_default_test_configuration,\
    get_default_storm_gateway

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class TestInfoProvider(unittest.TestCase):

    @patch('info_provider.glue.glue13.Glue13')
    @patch('info_provider.glue.glue2.Glue2')
    def test_configure(self, glue2_mock, glue13_mock):
        configuration = get_default_test_configuration()
        gateway = get_default_storm_gateway()
        ip = StormInfoProvider(configuration=configuration, gateway=gateway, glue13=glue13_mock, glue2=glue2_mock)
        ip.configure("all", "/tmp/report.json")

    @patch('info_provider.glue.glue13.Glue13')
    @patch('info_provider.glue.glue2.Glue2')
    def test_get_static_ldif(self, glue2_mock, glue13_mock):
        configuration = get_default_test_configuration()
        gateway = get_default_storm_gateway()
        ip = StormInfoProvider(configuration=configuration, gateway=gateway, glue13=glue13_mock, glue2=glue2_mock)
        ip.get_static_ldif("glue13")
        ip.get_static_ldif("glue2")

    @patch('info_provider.glue.glue13.Glue13')
    @patch('info_provider.glue.glue2.Glue2')
    def test_get_update_ldif(self, glue2_mock, glue13_mock):
        configuration = get_default_test_configuration()
        gateway = get_default_storm_gateway()
        ip = StormInfoProvider(configuration=configuration, gateway=gateway, glue13=glue13_mock, glue2=glue2_mock)
        ip.get_update_ldif("glue13")
        ip.get_update_ldif("glue2")

    def test_get_report_json(self):
        configuration = get_default_test_configuration()
        gateway = get_default_storm_gateway()
        ip = StormInfoProvider(configuration=configuration, gateway=gateway)
        ip.get_report_json("/tmp/report.json")

if __name__ == "__main__":
    unittest.main()