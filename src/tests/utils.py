import json
import os

from mock.mock import MagicMock

from info_provider.configuration import Configuration
from info_provider.model.space import SpaceRecord
from info_provider.storm_gateway import StormGateway

class MockHttpResponse:
    def __init__(self, data={}, code=200):
        self.code = code
        self.data = data

def get_test_configuration_filepath(filepath):
    return os.path.join(os.path.dirname(__file__), filepath)

def get_default_test_configuration_filepath():
    return get_test_configuration_filepath("resources/storm.def")

def get_incomplete_test_configuration_filepath():
    return get_test_configuration_filepath("resources/storm-incomplete.def")

def get_default_test_configuration():
    return Configuration(get_default_test_configuration_filepath())

def get_test_configuration(filepath):
    return Configuration(get_test_configuration_filepath(filepath))

def get_default_storm_gateway():
    configuration = get_default_test_configuration()
    gateway = StormGateway(configuration.get_backend_rest_endpoint())
    content = json.load(open(get_filepath("resources/response.json")))
    gateway.get_vfs_list = MagicMock(return_value=content)
    gateway.get_vfs_space_info = MagicMock(side_effect=get_sa_status_as_json)
    return gateway

def get_sa_status_as_json(sa_token):
    filepath = get_sa_status_filepath(sa_token)
    content = json.load(open(filepath))
    return content["sa-status"]

def get_sa_status_filepath(sa_token):
    if sa_token == "NESTED_TOKEN":
        filename = "resources/nested_status.json"
    if sa_token == "TESTVO_TOKEN":
        filename = "resources/testvo_status.json"
    if sa_token == "TESTVO2_TOKEN":
        filename = "resources/testvo2_status.json"
    if sa_token == "NOAUTH_TOKEN":
        filename = "resources/noauth_status.json"
    if sa_token == "TESTVOBIS_TOKEN":
        filename = "resources/testvobis_status.json"
    if sa_token == "TAPE_TOKEN":
        filename = "resources/tape_status.json"
    if sa_token == "IGI_TOKEN":
        filename = "resources/igi_status.json"
    if not filename:
        raise ValueError("Unexpected SA token")
    return get_filepath(filename)

def get_response_from_url(url):
    if "configuration" in url:
        return open(get_filepath("resources/response.json"))
    sa_token = url.split('/')[-1]
    return open(get_sa_status_filepath(sa_token))

def get_is_online_successful_response(url):
    return MockHttpResponse()

def get_filepath(filename):
    return os.path.join(os.path.dirname(__file__), filename)

def get_default_space_info_summary():
    return SpaceRecord(**{
        "total": 26000000000,
        "available": 25999971328,
        "used": 28672,
        "free": 25999971328,
        "unavailable": 0,
        "reserved": 0,
        "busy": 28672,
        "near_line": 8000000000
        })

def get_default_space_info_summary_from_configuration():
    return SpaceRecord(**{
        "total": 26000000000,
        "available": 26000000000,
        "used": 0,
        "free": 26000000000,
        "unavailable": 0,
        "reserved": 0,
        "busy": 0,
        "near_line": 8000000000
        })
