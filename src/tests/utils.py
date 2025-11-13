import json
import os

from info_provider.configuration import Configuration
from info_provider.model.space import SpaceRecord

def get_test_configuration_filepath(filepath):
    return os.path.join(os.path.dirname(__file__), filepath)

def get_default_test_configuration_filepath():
    return get_test_configuration_filepath("resources/test_srr.json")

def get_default_test_configuration():
    return Configuration(path=get_default_test_configuration_filepath())

def get_test_configuration(filepath):
    return Configuration(path=get_test_configuration_filepath(filepath))

def get_default_space_info_summary():
    return SpaceRecord(**{
        "total": 17307119365118,
        "used": 15485910760192,
        "free": 1821208604926,
        "reserved": 0,
        "near_line": 17307119365118
        })
