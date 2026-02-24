from tests.test_configuration import TestConfiguration
from tests.test_glue2 import TestGlue2
from tests.test_info_provider import TestInfoProvider
from tests.test_space_info import TestSpaceInfo
import unittest

import logging
import logging.config

logging.config.fileConfig("resources/logging.ini")


def create_suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestGlue2))
    suite.addTests(loader.loadTestsFromTestCase(TestInfoProvider))
    suite.addTests(loader.loadTestsFromTestCase(TestSpaceInfo))
    return suite


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(create_suite())
