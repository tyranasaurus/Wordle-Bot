from replit import db
import os
f = open("url.txt", "a")
f.write(os.getenv("REPLIT_DB_URL"))
f.close()
print('hi')
f = open("db.txt", "a")
for key, value in db.items():
	f.write(str(key)+": "+str(value)+'\n')
f.close()