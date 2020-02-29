from Logger import Logger
from HTTPRequest import HTTPRequest
import urllib.request


class HTTPProxyRequest(HTTPRequest):
    retry_limit = 5
    _response = None
    _proxy_manager = None

    @staticmethod
    def set_proxy_manager(proxy_manager):
        HTTPProxyRequest._proxy_manager = proxy_manager

    def read(self):
        if HTTPProxyRequest.retry_limit is not int:
            HTTPProxyRequest.retry_limit = 5
        try_count = 0
        response = ''
        while True:
            if try_count == HTTPProxyRequest.retry_limit:
                Logger.error('Could not retrieve page {}'.format(self._url))
                break
            proxy = HTTPProxyRequest._proxy_manager.get_proxy()
            try:
                Logger.message('Making request using proxy: {}'.format(self._url))
                self.set_proxy(proxy, 'http')
                self._response = urllib.request.urlopen(self, timeout=10)
                response = self._response.read().decode('utf-8')
                HTTPProxyRequest._proxy_manager.confirm_proxy(proxy)
                break
            except Exception as e:
                Logger.error('Exception occurred while reading response for url {}, message: {}'.format(self._url, e))
                HTTPProxyRequest._proxy_manager.remove_proxy(proxy)
            try_count += 1
        return response
