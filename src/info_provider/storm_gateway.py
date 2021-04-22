from http.client import HTTPException
import http.client
import json
import logging
import time
from urllib.error import HTTPError, URLError
import urllib.request, urllib.error, urllib.parse


class StormGateway:

    def __init__(self, endpoint):
        self._endpoint = endpoint
        self._max_attempts = 5

    def get_endpoint(self):
        return self._endpoint

    def get_vfs_space_info(self, sa_token):
        logging.debug("Getting space info for storage area %s ...", sa_token)
        url = self._endpoint + "/info/status/" + sa_token
        response = self._get_json(url)
        return response["sa-status"]

    def get_vfs_list(self):
        logging.debug("Retrieving backend configuration from %s ...", self._endpoint)
        url = self._endpoint + "/configuration/1.3/VirtualFSList"
        response = self._get_json(url)
        return response

    def get_vfs_list_with_status(self):
        vfs_list = self.get_vfs_list()
        for name, data in list(vfs_list.items()):
            logging.debug("retrieving space info data for %s", name)
            vfs_list[name]["space"] = self.get_vfs_space_info(data["token"])
        return vfs_list

    def is_online(self):
        url = self._endpoint + "/configuration/1.3/VirtualFSList"
        request = urllib.Request(url)
        request.get_method = lambda : 'HEAD'
        try:
            response = urllib.request.urlopen(request)
            return response.code == 200
        except HTTPError as e:
            logging.debug("HTTPError = " + str(e.code))
            return False
        except URLError as e:
            logging.debug("URLError = " + str(e.reason))
            return False
        except HTTPException as e:
            logging.debug("HTTPException")
            return False

    def _get_json(self, url):
        logging.debug("Getting JSON from URL: " + url)
        max_attempts = 5
        delay = 1  # sec
        attempt = 0
        while attempt <= max_attempts:
            attempt += 1
            logging.debug("Attempt %d/%d ...", attempt, max_attempts)
            try:
                response = urllib.request.urlopen(url)
                logging.debug("Response: %s", response)
                return json.load(response)
            except HTTPError as e:
                logging.error("HTTPError = " + str(e.code))
                self._retry_or_fail(e, url, attempt, delay)
            except URLError as e:
                logging.error("URLError = " + str(e.reason))
                self._retry_or_fail(e, url, attempt, delay)
            except HTTPException as e:
                logging.error("HTTPException")
                self._retry_or_fail(e, url, attempt, delay)
            delay *= 2

    def _retry_or_fail(self, ex, url, attempt, delay):
        if attempt == self._max_attempts:
            logging.error("Unable to contact %s after %d attempts", url, attempt)
            raise ex
        logging.warning("Unable to contact %s - %s seconds to the next attempt ...", url, delay)
        time.sleep(delay)