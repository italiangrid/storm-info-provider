import logging

from info_provider.storm_space_info_builder import SpaceInfoBuilder
from tests.utils import get_default_test_configuration, get_default_space_info_summary

import unittest

logger = logging.getLogger(__name__)

class TestSpaceInfo(unittest.TestCase):

    def test_space_info_builder_with_default_configuration(self):
        configuration = get_default_test_configuration()
        spaceinfo = SpaceInfoBuilder(configuration).build()
        expected_summary = get_default_space_info_summary()
        self.assertEqual(spaceinfo.get_summary().get_total(), expected_summary.get_total())
        self.assertEqual(spaceinfo.get_summary().get_used(), expected_summary.get_used())
        self.assertEqual(spaceinfo.get_summary().get_free(), expected_summary.get_free())
        self.assertEqual(spaceinfo.get_summary().get_reserved(), expected_summary.get_reserved())
        self.assertEqual(spaceinfo.get_summary().get_nearline(), expected_summary.get_nearline())
