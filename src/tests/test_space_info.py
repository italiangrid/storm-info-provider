from info_provider.storm_space_info_builder import SpaceInfoBuilder
from tests.utils import get_default_test_configuration,\
    get_default_storm_gateway, get_default_space_info_summary,\
    get_default_space_info_summary_from_configuration


try:
    import unittest2 as unittest
except ImportError:
    import unittest

class TestSpaceInfo(unittest.TestCase):

    def test_space_info_builder_with_default_configuration(self):
        configuration = get_default_test_configuration()
        gateway = get_default_storm_gateway()
        spaceinfo = SpaceInfoBuilder(configuration, gateway).build()
        expected_summary = get_default_space_info_summary()
        self.assertEqual(spaceinfo.get_summary().get_total(), expected_summary.get_total())
        self.assertEqual(spaceinfo.get_summary().get_available(), expected_summary.get_available())
        self.assertEqual(spaceinfo.get_summary().get_used(), expected_summary.get_used())
        self.assertEqual(spaceinfo.get_summary().get_free(), expected_summary.get_free())
        self.assertEqual(spaceinfo.get_summary().get_unavailable(), expected_summary.get_unavailable())
        self.assertEqual(spaceinfo.get_summary().get_reserved(), expected_summary.get_reserved())
        self.assertEqual(spaceinfo.get_summary().get_busy(), expected_summary.get_busy())
        self.assertEqual(spaceinfo.get_summary().get_nearline(), expected_summary.get_nearline())

    def test_space_info_builder_with_default_configuration_but_serving_state_closed(self):
        configuration = get_default_test_configuration()
        configuration.set("STORM_SERVING_STATE", "closed")
        gateway = get_default_storm_gateway()
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