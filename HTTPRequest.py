from Logger import Logger
import urllib.request
import urllib.response
import urllib.parse
import urllib.error
import socket


class HTTPRequest(urllib.request.Request):
    headers = {}
    _url = None
    _response = None

    def __init__(self, url, form_data=None):
        self._url = url
        if not form_data:
            super().__init__(url, headers=HTTPRequest.headers)
        else:
            super().__init__(url, urllib.parse.urlencode(form_data), HTTPRequest.headers)

    def read(self):
        try:
            self._response = urllib.request.urlopen(self, timeout=10)
            return self._response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            Logger.error('HTTP ERROR: {}'.format(e))
        except urllib.error.URLError as e:
            Logger.error('URLLIB ERROR: {}'.format(e))
        except socket.timeout as e:
            Logger.error('Connection timed out, message: {}'.format(e))
        except Exception as e:
            Logger.error('Exception occurred while reading response for url "{}", message: {}'.format(self._url, e))
        return ''
