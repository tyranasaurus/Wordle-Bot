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

for player_id, player in db['players'].items():
	stats_dict = build_stats()
	for game_id, game in player['games'].items():
		if not game:
			del player['games'][game_id]
		else:
			update_stats(stats_dict, game)
	player['stats'] = stats_dict
for game_id, game_dict in db['games'].items():
	stats_dict = build_stats()
	for player_id, game in game_dict['games'].items():
		update_stats(stats_dict, game)
	game_dict['stats'] = stats_dict