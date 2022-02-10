
from replit import db
def build_stats():
	return {
		'won': 0,
		'lost': 0,
		'played': 0,
		'score': 0,
		'guesses': 0,
		'saverage': 0,
		'winrate': 0,
		'green': 0,
		'gaverage': 0,
		'yellow': 0,
		'yaverage': 0,
		'black': 0,
		'baverage': 0
	}
def build_player(name):
	return {
		'games': {},
		'name': name,
		'stats': build_stats()
	}

db['guilds']={}
db['players']={}
print(db['players'])
for player_id, player_dict in db.items():
	db['players'][player_id]=player_dict
	#del db[player_id]
print(db.keys())
print(db['players'].keys())
for player_id, player_dict in db.items():
	if player_id != 'players':
		del db[player_id]
'''
guild_id = "735593986432958685"
new_dict = {}
for key, value in db.items():
    new_dict[key] = value
for key in db.keys():
	del db[key]
db[guild_id] = new_dict
'''
#del db["233740786125111297"]
'''
for player_id, player_dict in db.items():
	try:
		name = player_dict['stats']['player']
	except KeyError:
		continue
	games = player_dict['game_ids']
	player = build_player(name)
	for game_id in games:
		player['games'][game_id] = None
	stats = player['stats']
	stats['won'] = player_dict['won']
	stats['lost'] = player_dict['lost']
	stats['played'] = player_dict['stats']['played']
	stats['score'] = round(player_dict['stats']['score'] * player_dict['stats']['played'])
	stats['guesses'] = player_dict['rows']
	stats['saverage'] = player_dict['stats']['score']
	stats['winrate'] = player_dict['stats']['winrate']
	stats['green'] = player_dict['green']
	stats['yellow'] = player_dict['yellow']
	stats['black'] = player_dict['black']
	stats['gaverage'] = round(player_dict['green'] / player_dict['rows'], 2)
	stats['yaverage'] = round(player_dict['yellow'] / player_dict['rows'], 2)
	stats['baverage'] = round(player_dict['black'] / player_dict['rows'], 2)
	db[player_id] = player
'''
'''
count = 0
for key, player_dict in db.items():
	count += 1
	game_dict = {}
	for game in player_dict['game_ids']:
		game_dict[game] = None
	#player_dict['game_ids'] = game_dict
	print(player_dict)
	print(game_dict)
print(count)
'''
	
import os
print(os.getenv("REPLIT_DB_URL"))