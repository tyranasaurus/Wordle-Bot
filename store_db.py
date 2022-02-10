from replit import db
print('hi')
f = open("db.txt", "a")
for key, value in db.items():
	f.write(str(key)+": "+str(value)+'\n')

f.close()