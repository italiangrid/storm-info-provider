try:
    import json
except ImportError:
    import simplejson as json
import urllib2
import logging
import time
import sys
import string
import fileinput
import os
import re

def clear_quotes(s):
    return s.replace('\"','').replace("\'",'')

def clear_newlines(s):
    return s.replace("\n",'')

def clean_dns_like_chars(s):
    return s.replace('.','').replace('-','').replace('_','')

def http_get(url, max_attempts=5, min_delay=1):
    seconds = min_delay
    attempt = 0
    # logging.info('GET %s', url)
    while attempt < max_attempts:
        try:
            response = urllib2.urlopen(url)
            #logging.info('200 OK')
            return response
        except Exception, ex:
            logging.error('%s', ex)
            # try again?
            attempt += 1
            if attempt == max_attempts:
                sys.exit('Unable to contact ' + url + ' after ' + str(attempt) + ' attempts')
            logging.info('Retrying after %s seconds...', seconds)
            time.sleep(seconds)
            seconds *= 2
    sys.exit('Unable to contact ' + url)
    return ""

def get_vfs_space_info_from_BE(be_host, be_port, sa_token):
    url = 'http://' + be_host + ':' + str(be_port) + '/info/status/' + sa_token
    data = json.load(http_get(url))
    logging.debug("GET %s = %s", url, data)
    return data["sa-status"]

def get_vfs_list_from_BE(be_host, be_port):
    url = 'http://' + be_host + ':' + str(be_port) + '/configuration/1.3/VirtualFSList' 
    data = json.load(http_get(url))
    logging.debug("GET %s = %s", url, data)
    return data
    
def load_configuration_from_file(filepath):
    configuration = {}
    try:
        f = open(filepath, 'r')
        for line in f:
            (key, val) = line.split('=')
            configuration[key] = clear_quotes(clear_newlines(val.strip()))
    finally:
        f.close()
        logging.debug('loaded configuration = %s', configuration)
    return configuration

def are_keys_in_dictionary(dic, keys):
    for key in keys:
        if not key in dic:
            return False
    return True

def change_line_in_a_file(file_target, line_pattern, line_new):
    for line in fileinput.input(file_target):
        if line_pattern in line:
            line.replace(line, line_new)
    return

def round_div(num, value):
    return int(round(1.0 * num/value))

def delete_files(parent_directory, pattern):
    removed_list = []
    for f in os.listdir(parent_directory):
        if re.search(pattern,f):
            os.remove(os.path.join(parent_directory, f))
            removed_list.append(f)
    return removed_list
