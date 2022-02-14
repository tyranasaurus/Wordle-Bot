from replit import db

def update_stats(stats, game):
	if game['win']:
		stats['won'] += 1
	else:
		stats['lost'] += 1
	stats['played'] += 1
	stats['score'] += game['score']
	stats['guesses'] += game['guesses']
	stats['winrate'] = int(round(stats['won'] / stats['played'], 2)*100)
	stats['green'] += game['green']
	stats['yellow'] += game['yellow']
	stats['black'] += game['black']
	stats['saverage'] = round(stats['score'] / stats['played'], 2)
	stats['gaverage'] = round(stats['green'] / stats['guesses'] , 2)
	stats['yaverage'] = round(stats['yellow'] / stats['guesses'], 2)
	stats['baverage'] = round(stats['black'] / stats['guesses'], 2)
	return

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
def build_game():
	return {
		'games': {},
		'stats': build_stats()
	}
'''
try:
	del db['games']
except:
	print("No database")
db['games'] = {}
'''
for player_id, player in db['players'].items():
	try:
		print(player['name'])
	except KeyError:
		print(player)
	for game_id, player_game in player['games'].items():
		if not player_game:
			continue
		#print(game_id)
		try:
			game = db['games'][game_id]
			#print('old')
		except KeyError:
			game = build_game()
			#print('new')
		try:
			if game['games'][player_id]:
				continue
		except KeyError:
			pass
		game['games'][player_id] = player_game
		update_stats(game['stats'], player_game)
		db['games'][game_id] = game
	
		