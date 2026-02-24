from mock.mock import patch

from info_provider.storm_info_provider import StormInfoProvider
from tests.utils import get_default_test_configuration

import unittest


class TestInfoProvider(unittest.TestCase):
    @patch("info_provider.glue.glue2.Glue2")
    def test_configure(self, glue2_mock):
        configuration = get_default_test_configuration()
        ip = StormInfoProvider(configuration=configuration, glue2=glue2_mock)
        ip.configure()

    @patch("info_provider.glue.glue2.Glue2")
    def test_get_static_ldif(self, glue2_mock):
        configuration = get_default_test_configuration()
        ip = StormInfoProvider(configuration=configuration, glue2=glue2_mock)
        ip.get_static_ldif()

    @patch("info_provider.glue.glue2.Glue2")
    def test_get_update_ldif(self, glue2_mock):
        configuration = get_default_test_configuration()
        ip = StormInfoProvider(configuration=configuration, glue2=glue2_mock)
        ip.get_update_ldif()


if __name__ == "__main__":
    unittest.main()
