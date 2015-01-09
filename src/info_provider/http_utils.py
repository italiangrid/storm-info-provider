import urllib2
import logging
import time

try:
    import json
except ImportError:
    import simplejson as json

class HTTP:

    def __init__(self):
        self.max_attempts = 5
        self.min_delay = 1 # sec
        return

    def getJSON(self, url):
        seconds = self.min_delay
        attempt = 0
        while attempt < self.max_attempts:
            try:
                response = urllib2.urlopen(url)
                return json.load(response)
            except Exception, ex:
                # try again?
                attempt += 1
                if attempt == self.max_attempts:
                    raise Exception('Network error: Unable to contact ' + 
                        url + ' after ' + str(attempt) + ' attempts')
                logging.warning('Unable to contact %s - %s seconds to the next attempt ...', url, seconds)
                time.sleep(seconds)
                seconds *= 2
        raise Exception('Network error: Unable to contact ' + url)