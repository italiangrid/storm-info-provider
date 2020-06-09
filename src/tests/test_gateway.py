from httplib import HTTPException
from urllib2 import HTTPError, URLError

from info_provider.storm_gateway import StormGateway
from tests.utils import *
from mock.mock import patch, MagicMock

import logging

try:
    import unittest2 as unittest
except ImportError:
    import unittest

class TestGateway(unittest.TestCase):

    def setUp(self):
        self._configuration = get_default_test_configuration()
        endpoint = self._configuration.get_backend_rest_endpoint()
        self._gateway = StormGateway(endpoint)
        self.assertEqual(self._gateway.get_endpoint(), endpoint)

    @patch('info_provider.storm_gateway.urllib2')
    def test_with_successful_remote_call(self, mock_urllib2):
        logging.debug("Testing gateway with successful mocked response ...")
        mock_urllib2.urlopen = MagicMock(side_effect=get_response_from_url)
        response = self._gateway.get_vfs_list_with_status()
        self.assertEqual(len(response.items()), 7)
        for name, data in response.items():
            logging.debug("%s: %s", name, data)

    @patch('info_provider.storm_gateway.urllib2')
    def test_is_online(self, mock_urllib2):
        logging.debug("Testing gateway is_online with successful mocked response ...")
        mock_urllib2.urlopen = MagicMock(side_effect=get_is_online_successful_response)
        response = self._gateway.is_online()
        self.assertEqual(response, True)

    @patch('info_provider.storm_gateway.urllib2')
    def test_is_offline(self, mock_urllib2):
        logging.debug("Testing gateway is_online with error response ...")
        mock_urllib2.urlopen = MagicMock(side_effect=TestGateway.raise_http_error)
        response = self._gateway.is_online()
        self.assertEqual(response, False)
        mock_urllib2.urlopen = MagicMock(side_effect=TestGateway.raise_url_error)
        response = self._gateway.is_online()
        self.assertEqual(response, False)
        mock_urllib2.urlopen = MagicMock(side_effect=TestGateway.raise_http_exception)
        response = self._gateway.is_online()
        self.assertEqual(response, False)

    @patch('info_provider.storm_gateway.urllib2')
    def test_http_error(self, mock_urllib2):
        logging.debug("Testing HTTPError ...")
        mock_urllib2.urlopen.side_effect = TestGateway.raise_http_error
        try:
            self._gateway.get_vfs_list_with_status()
            self.fail("HTTPError expected")
        except HTTPError as ex:
            logging.debug("Received HTTPError: %d %s" % (ex.code, ex.reason))
            self.assertEqual(ex.code, 500)
            self.assertEqual(ex.reason, "Bad Gateway")

    @patch('info_provider.storm_gateway.urllib2')
    def test_url_error(self, mock_urllib2):
        logging.debug("Testing URLError ...")
        mock_urllib2.urlopen.side_effect = TestGateway.raise_url_error
        try:
            self._gateway.get_vfs_list_with_status()
            self.fail("URLError expected")
        except URLError as ex:
            logging.debug("Received URLError: %s" % (ex.reason))
            self.assertTrue("Malformed URL" in ex.reason)

    @patch('info_provider.storm_gateway.urllib2')
    def test_http_exception(self, mock_urllib2):
        logging.debug("Testing HTTPException ...")
        mock_urllib2.urlopen.side_effect = TestGateway.raise_http_exception
        try:
            self._gateway.get_vfs_list_with_status()
            self.fail("HTTPException expected")
        except HTTPException as ex:
            logging.debug("Received HTTPException: %s" % (ex))
            self.assertTrue("HTTPException on getting URL: " in ex.message)

    @staticmethod
    def raise_http_error(url):
        raise HTTPError(url=url, code=500, msg="Bad Gateway", hdrs=None, fp=None)

    @staticmethod
    def raise_url_error(url):
        raise URLError("Malformed URL " + url)

    @staticmethod
    def raise_http_exception(url):
        raise HTTPException("HTTPException on getting URL: " + url)

if __name__ == "__main__":
    unittest.main()
