from Logger import Logger
from HTTPRequest import HTTPRequest
import random
import time


class ProxyManager(object):
	proxy_alert_count = 3
	_proxies = []
	_suspect_proxies = []
	_deleted_proxies = []
	_proxies_list_url = None

	def set_url(self, url):
		self._proxies_list_url = url

	def update_proxies(self, wait=True):
		Logger.message('ProxyManager: Updating proxy list')
		proxy_list = HTTPRequest(self._proxies_list_url).read().splitlines(False)
		if len(proxy_list) == 0:
			Logger.error('ProxyManager: Could not retrieve proxy list from server')
		if len(proxy_list) == 1:
			if wait:
				Logger.message('ProxyManager: Waiting for access to proxy list')
				time.sleep(30)
				self.update_proxies()
			return
		for proxy in proxy_list:
			if proxy not in self._proxies:
				self._proxies.append(proxy)
				if proxy in self._deleted_proxies:
					Logger.message('ProxyManager: Added previously removed proxy {} as suspicious'.format(proxy))
					self._suspect_proxies.append(proxy)
				else:
					Logger.message('ProxyManager: Added proxy {}'.format(proxy))
		if len(self._proxies) == 0:
			Logger.error('ProxyManager: Proxy list is empty')
			return False
		return True

	def get_proxy(self) -> str:
		proxies_count = len(self._proxies)
		if proxies_count == 0:
			Logger.error('ProxyManager: No available proxies')
			if not self.update_proxies():
				raise Exception('ProxyManager: Updating proxy list failed')
			return self.get_proxy()
		return self._proxies[random.randint(0, proxies_count - 1)]

	def remove_proxy(self, proxy):
		if proxy in self._proxies:
			if proxy in self._suspect_proxies:
				Logger.message('ProxyManager: Removing proxy {} from list'.format(proxy))
				try:
					self._suspect_proxies.remove(proxy)
					self._proxies.remove(proxy)
				except ValueError:
					pass
				self._deleted_proxies.append(proxy)
			else:
				Logger.message('ProxyManager: Marking proxy {} as suspicious'.format(proxy))
				self._suspect_proxies.append(proxy)
		proxies_count = len(self._proxies)
		if proxies_count <= ProxyManager.proxy_alert_count:
			Logger.message('ProxyManager: Only {} proxies left on list'.format(proxies_count))
			self.update_proxies(False)

	def confirm_proxy(self, proxy):
		if proxy in self._suspect_proxies:
			Logger.message('ProxyManager: Marking proxy {} as non suspicious'.format(proxy))
			self._suspect_proxies.remove(proxy)
