import json


database = open('output.txt', 'r', encoding='utf-8').read().splitlines(False)
database_new = open('email_list.txt', 'w', encoding='utf-8')
email_list = []

for row in database:
	if len(row) == 0:
		break
	data = json.loads(row)
	if data['type'] == 'user_data' and data['email'] != '' and data['email'] not in email_list:
		email_list.append(data['email'])
		database_new.write(data['email'] + '\n')
