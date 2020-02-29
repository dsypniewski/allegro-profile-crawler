from Logger import Logger
from ConsoleLogger import ConsoleLogger
from HTTPRequest import HTTPRequest
from HTTPProxyRequest import HTTPProxyRequest
from ProxyManager import ProxyManager
import multiprocessing
import multiprocessing.managers
import json
import re

regex_email = '([A-Z0-9%+\-\._]+@[A-Z0-9\.\-_]+\.[A-Z0-9]+)'
regex_category_id = 'Shop\.php/Listing\?category=([0-9]+)'
regex_category_page = 'Shop\.php/Listing\?category=[0-9]+&p=([0-9]+)'
regex_about_user_link = 'my_page\.php\?uid=([0-9]+)'
regex_auction_link = '"(/.*?\.html)"'
regex_user_name = '\<span class="uname"\>(.*?)\</span\>'
allegro_category_url = 'http://allegro.pl/Shop.php/Listing?category='
allegro_about_user_url = 'http://allegro.pl/my_page.php?uid='
allegro_user_auctions_url = 'http://allegro.pl/listing/user/listing.php?us_id='

processes_no = 5
ProxyManager.proxy_alert_count = 5
HTTPProxyRequest.headers = HTTPRequest.header = {'User-agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.57 Safari/537.36'}
proxy_list_url = ''  # URL for a proxy list

Logger.init()
ConsoleLogger.init()


class MyManager(multiprocessing.managers.BaseManager):
	pass


def parse_user_page(worker_id, uid):
	Logger.message('Worker {}: processing user with id: {}'.format(worker_id, uid))
	request = HTTPProxyRequest(allegro_about_user_url + str(uid))
	response_0 = request.read()
	email_list = re.findall(regex_email, response_0, re.IGNORECASE)
	user_name = re.findall(regex_user_name, response_0, re.IGNORECASE)
	if len(user_name) == 0:
		user_name = ''
	else:
		user_name = user_name[0]
	if len(email_list) == 0:
		Logger.message('Worker {}: requesting user page, user id: {}'.format(worker_id, uid))
		request = HTTPProxyRequest(allegro_user_auctions_url + str(uid))
		auctions = re.findall(regex_auction_link, request.read(), re.IGNORECASE)
		if len(auctions) > 0:
			Logger.message('Worker {}: requesting user auction, user id: {}'.format(worker_id, uid))
			request = HTTPProxyRequest('http://allegro.pl' + auctions[0])
			email_list = re.findall(regex_email, request.read(), re.IGNORECASE)
		else:
			email_list = []
	return user_name, email_list


def parse_categories(worker_id, input_queue, output_queue, proxy_manager, done_user_list, done_categories_list):
	try:
		HTTPProxyRequest.set_proxy_manager(proxy_manager)
		Logger.message('Worker {}: started'.format(worker_id))
		while True:
			Logger.message('Worker {}: trying to acquire job'.format(worker_id))
			category_id = input_queue.get()
			if category_id is None:
				Logger.message('Worker {}: found poison pill, terminating'.format(worker_id))
				input_queue.task_done()
				break
			Logger.message('Worker {}: processing category id {}'.format(worker_id, category_id))
			if (category_id in done_categories_list) and ('all' in done_categories_list[category_id]):
				Logger.message('Worker {}: category {} was already processed'.format(worker_id, category_id))
				continue
			response = HTTPProxyRequest(allegro_category_url + str(category_id)).read()
			m = re.findall(regex_category_page, response, re.IGNORECASE)
			if len(m) == 0:
				Logger.message('Worker {}: category {} is empty'.format(worker_id, category_id))
				output_queue.put({'type': 'category_data', 'category_id': category_id, 'page': 'all'})
				input_queue.task_done()
				continue
			pages = int(m[-1])
			for page_no in range(1, pages + 1):
				Logger.message('Worker {}: started processing page {} of {} from category {}'.format(worker_id, page_no, pages, category_id))
				if (category_id in done_categories_list) and (page_no in done_categories_list[category_id]):
					Logger.message('Worker {}: page {} in category {} was already processed'.format(worker_id, page_no, category_id))
					continue
				if page_no > 1:
					response = HTTPProxyRequest(allegro_category_url + str(category_id) + '&p=' + str(page_no)).read()
				user_ids = re.findall(regex_about_user_link, response, re.IGNORECASE)
				for user_id in user_ids:
					if user_id in done_user_list:
						Logger.message('Worker {}: user {} already processed'.format(worker_id, user_id))
						continue
					(user_login, email_list) = parse_user_page(worker_id, user_id)
					email_list = set(email_list)
					Logger.message('Worker {}: found {} emails for uid {}'.format(worker_id, len(email_list), user_id))
					if len(email_list) == 0:
						output_queue.put({'type': 'user_data', 'user_id': user_id, 'login': user_login, 'email': ''})
					else:
						for email in email_list:
							output_queue.put({'type': 'user_data', 'user_id': user_id, 'login': user_login, 'email': email})
					done_user_list.append(user_id)
				output_queue.put({'type': 'category_data', 'category_id': category_id, 'page': page_no})
				Logger.message('Worker {}: finished processing page {} of {} from category {}'.format(worker_id, page_no, pages, category_id))
			output_queue.put({'type': 'category_data', 'category_id': category_id, 'page': 'all'})
			Logger.message('Worker {}: done processing category id {}'.format(worker_id, category_id))
			input_queue.task_done()
		Logger.message('Worker {}: finished'.format(worker_id))
	except KeyboardInterrupt:
		pass


def output_handler(output_queue):
	output_file = open('output.txt', 'a', encoding='utf-8')
	try:
		while True:
			item = output_queue.get()
			if item is None:
				break
			output_file.write(json.dumps(item) + '\n')
			output_file.flush()
	except KeyboardInterrupt:
		pass
	finally:
		output_file.flush()
		output_file.close()


def main():
	Logger.message('Start')
	# Find all categories ids
	response = HTTPRequest(allegro_category_url + '0').read()
	matches = re.findall(regex_category_id, response, re.IGNORECASE)
	main_categories = set(matches)
	main_categories.add('0')
	categories_ids = []
	for category_id in matches:
		Logger.message('Collecting categories ids in category: {}'.format(category_id))
		response = HTTPRequest(allegro_category_url + category_id).read()
		id_list = re.findall(regex_category_id, response, re.IGNORECASE)
		for sub_cat_id in id_list:
			if sub_cat_id not in main_categories:
				categories_ids.append(sub_cat_id)

	# Create queues
	input_queue = multiprocessing.JoinableQueue()
	output_queue = multiprocessing.Queue()

	# Fill input queue
	for category_id in categories_ids:
		input_queue.put(category_id)

	Logger.message('Queue size: {}'.format(input_queue.qsize()))

	# Create proxy manager
	MyManager.register('ProxyManagerClass', ProxyManager)
	manager = MyManager()
	manager.start()
	proxy_manager = manager.ProxyManagerClass()
	proxy_manager.set_url(proxy_list_url)
	proxy_manager.update_proxies()

	# Create processed user list
	user_list = multiprocessing.Manager().list()

	# Create categories dictionary
	categories_list = multiprocessing.Manager().dict()

	# Get list of already processed items
	try:
		database = open('output.txt', 'r', encoding='utf-8').read().splitlines(False)
		for row in database:
			data = json.loads(row)
			if data['type'] == 'user_data':
				if data['user_id'] not in user_list:
					user_list.append(data['user_id'])
			elif data['type'] == 'category_data':
				if data['category_id'] not in categories_list:
					categories_list[data['category_id']] = []
				tmp = categories_list[data['category_id']]
				if data['page'] not in tmp:
					tmp.append(data['page'])
					categories_list[data['category_id']] = tmp
	except IOError:
		pass

	Logger.message('Already processed {} users'.format(len(user_list)))

	# Create worker processes
	processes = []
	Logger.message('Starting worker processes.')
	for worker_id in range(processes_no):
		# Add poison pill for each process
		input_queue.put(None)
		process = multiprocessing.Process(target=parse_categories,
			args=(worker_id, input_queue, output_queue, proxy_manager, user_list, categories_list), daemon=True)
		processes.append(process)
		process.start()

	# Setup finish flag for output handler

	# Create output handler process
	Logger.message('Starting output handler process.')
	output_process = multiprocessing.Process(target=output_handler, args=(output_queue,), daemon=True)
	output_process.start()

	# Wait for worker processes to finish
	Logger.message('Waiting for worker processes to finish.')
	try:
		for process in processes:
			process.join()
	except KeyboardInterrupt:
		pass
	finally:
		# Put poison pill for output handler
		output_queue.put(None)

	Logger.message('Done loading, waiting for output handler process to finish.')

	# Wait for output handler to finish
	output_process.join()


if __name__ == '__main__':
	main()
