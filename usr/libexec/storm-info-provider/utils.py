
import urllib2
import logging
import time
import string
import os
import re

def clear_quotes(s):
    return s.replace('\"','').replace("\'",'')

def clear_newlines(s):
    return s.replace("\n",'')

#def clean_dns_like_chars(s):
#    return s.replace('.','').replace('-','').replace('_','')

def http_get(url, max_attempts=5, min_delay=1):
    seconds = min_delay
    attempt = 0
    while attempt < max_attempts:
        try:
            response = urllib2.urlopen(url)
            return response
        except Exception, ex:
            logging.error('%s', ex)
            # try again?
            attempt += 1
            if attempt == max_attempts:
                raise Exception('HTTP-GET error: Unable to contact ' + url + ' after ' + str(attempt) + ' attempts')
            logging.info('Retrying after %s seconds...', seconds)
            time.sleep(seconds)
            seconds *= 2
    raise Exception('HTTP-GET error: Unable to contact ' + url)

def round_div(num, value):
    return int(round(1.0 * num/value))

def delete_files(parent_directory, pattern):
    removed_list = []
    for f in os.listdir(parent_directory):
        if re.search(pattern,f):
            os.remove(os.path.join(parent_directory, f))
            removed_list.append(f)
    return removed_list
