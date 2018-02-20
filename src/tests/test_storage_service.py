import json

from mock.mock import patch

from info_provider.storm_storage_service_builder import StorageServiceBuilder
from tests.utils import get_default_test_configuration,\
    get_default_space_info_summary_from_configuration
from info_provider.storm_gateway import StormGateway
from tests.test_gateway import TestGateway
from info_provider.storm_space_info_builder import SpaceInfoBuilder

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class TestStorageService(unittest.TestCase):

    @patch('info_provider.model.space.SpaceInfo')
    @patch('info_provider.configuration.Configuration')
    def test_storage_service_builder(self, configuration, space_info):
        # setup configuration mock
        configuration.get_sitename.return_value = "test"
        configuration.get_implementation_version.return_value = "1.11.13"
        configuration.get_quality_level.return_value = "production"
        configuration.get_public_srm_endpoint.return_value = "frontend.hostname.org"
        configuration.get_public_http_endpoint.return_value = "webdav.hostname.org"
        configuration.get_public_https_endpoint.return_value = "ssl.webdav.hostname.org"
        # setup space_info mock
        space_info.get_vfs_list_with_status.return_value = {}
        # build storage service and check results
        service = StorageServiceBuilder(configuration, space_info).build()
        self.assertEqual(service.get_name(), configuration.get_sitename())
        self.assertEqual(service.get_implementation(), "storm")
        self.assertEqual(service.get_implementation_version(), configuration.get_implementation_version())
        self.assertEqual(service.get_quality_level(), configuration.get_quality_level())
        self.assertNotEqual(service.get_capabilities().index("data.management.transfer"), -1)
        self.assertNotEqual(service.get_capabilities().index("data.management.storage"), -1)
        self.assertIsNotNone(service.get_latest_update())
        self.assertEqual(len(service.get_shares()), 0)
        self.assertEqual(len(service.get_endpoints()), 3)
        # SRM
        self.assertEqual(service.get_endpoints()[0].get_url(), configuration.get_public_srm_endpoint())
        self.assertEqual(service.get_endpoints()[0].get_type(), "srm")
        self.assertEqual(service.get_endpoints()[0].get_version(), "2.2")
        self.assertEqual(service.get_endpoints()[0].get_name(), configuration.get_sitename() + "_srm")
        self.assertEqual(service.get_endpoints()[0].get_quality_level(), configuration.get_quality_level())
        self.assertNotEqual(service.get_endpoints()[0].get_capabilities().index("data.management.transfer"), -1)
        self.assertNotEqual(service.get_endpoints()[0].get_capabilities().index("data.management.storage"), -1)
        self.assertEqual(service.get_endpoints()[0].get_assigned_shares(), ["all"])
        # HTTP
        self.assertEqual(service.get_endpoints()[1].get_url(), configuration.get_public_http_endpoint())
        self.assertEqual(service.get_endpoints()[1].get_type(), "DAV")
        self.assertEqual(service.get_endpoints()[1].get_version(), "1.1")
        self.assertEqual(service.get_endpoints()[1].get_name(), configuration.get_sitename() + "_http")
        self.assertEqual(service.get_endpoints()[1].get_quality_level(), configuration.get_quality_level())
        self.assertNotEqual(service.get_endpoints()[1].get_capabilities().index("data.management.transfer"), -1)
        self.assertNotEqual(service.get_endpoints()[1].get_capabilities().index("data.management.storage"), -1)
        self.assertEqual(service.get_endpoints()[1].get_assigned_shares(), ["all"])
        # HTTPS
        self.assertEqual(service.get_endpoints()[2].get_url(), configuration.get_public_https_endpoint())
        self.assertEqual(service.get_endpoints()[2].get_type(), "DAV")
        self.assertEqual(service.get_endpoints()[2].get_version(), "1.1")
        self.assertEqual(service.get_endpoints()[2].get_name(), configuration.get_sitename() + "_https")
        self.assertEqual(service.get_endpoints()[2].get_quality_level(), configuration.get_quality_level())
        self.assertNotEqual(service.get_endpoints()[2].get_capabilities().index("data.management.transfer"), -1)
        self.assertNotEqual(service.get_endpoints()[2].get_capabilities().index("data.management.storage"), -1)
        self.assertEqual(service.get_endpoints()[2].get_assigned_shares(), ["all"])
        # check it's a valid JSON string
        json.loads(service.to_json())

    @patch('info_provider.storm_gateway.urllib2')
    def test_storage_service_builder_when_remote_gateway_has_http_error(self, mock_urllib2):
        configuration = get_default_test_configuration()
        gateway = StormGateway(configuration.get_backend_rest_endpoint())
        mock_urllib2.urlopen.side_effect = TestGateway.raise_http_error
        spaceinfo = SpaceInfoBuilder(configuration, gateway).build()
        expected_summary = get_default_space_info_summary_from_configuration()
        self.assertEqual(spaceinfo.get_summary().get_total(), expected_summary.get_total())
        self.assertEqual(spaceinfo.get_summary().get_available(), expected_summary.get_available())
        self.assertEqual(spaceinfo.get_summary().get_used(), expected_summary.get_used())
        self.assertEqual(spaceinfo.get_summary().get_free(), expected_summary.get_free())
        self.assertEqual(spaceinfo.get_summary().get_unavailable(), expected_summary.get_unavailable())
        self.assertEqual(spaceinfo.get_summary().get_reserved(), expected_summary.get_reserved())
        self.assertEqual(spaceinfo.get_summary().get_busy(), expected_summary.get_busy())
        self.assertEqual(spaceinfo.get_summary().get_nearline(), expected_summary.get_nearline())