import json
from replit import db
import os
import pickle

dbt = {}
for key, value, in db.values():
	dbt[key] = value

db.db_url = ""

for key, value in dbt.values():
	db[key] = value



'''
global my_dict
my_dict = {}

test_dict = {'1':1, '2':2, '3':3}

with open('my_dict.pkl', 'wb') as f:
	for key, value in db.items():
		my_dict[key] = value
	pickle.dump(test_dict, f)
	print(my_dict)
	pickle.dump(my_dict, f)

with open('my_dict.json', 'w') as f:
	json.dump(my_dict, f)

'''
'''
f = open("url.txt", "a")
f.write(os.getenv("REPLIT_DB_URL"))
f.close()
f = open("db.txt", "a")
for key, value in db.items():
	f.write(str(key)+": "+str(value)+'\n')
f.close()
'''