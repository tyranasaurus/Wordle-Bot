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

def remove_game(player_id, game_id):
	try:
		player = db['players'][player_id]
		print('player exists')
		try:
			player_game = player['games'][game_id]
			print('game exists')
			player_stats = db['players'][player_id]['stats']
			if player_stats['played'] == 1:
				print('last game')
				del db['players'][player_id]
			else:
				print('remove player stats')
				remove_game_stats(player_stats, player_game)
				del player['games'][game_id]
		except KeyError:
			print("Can't find game:", game_id)
		
	except KeyError:
		print("Can't find player:", player_id)
	
	try:
		game_dict = db['games'][game_id]
		print('game dict exists')
		try:
			game_dict_game = game_dict['games'][player_id]
			game_stats = db['games'][game_id]['stats']
			if game_stats['played'] == 1:
				print('last game')
				del db['games'][game_id]
			else:
				print('remove game stats')
				remove_game_stats(game_stats, game_dict_game)
				del game_dict['games'][player_id]
		except KeyError:
			print("Can't find game for player:", player_id)
		
	except KeyError:
		print("Can't find game dict:", game_id)
'''
for player_id, player in db['players'].items():
	print(player['name'])
	stats_dict = build_stats()
	remove = []
	for game_id, game in player['games'].items():
		if not game:
			remove.append(game_id)
		else:
			update_stats(stats_dict, game)
	for game_id in remove:
		print(game_id)
		del player['games'][game_id]
	if not player['games']:
		del db['players'][player_id]
	player['stats'] = stats_dict
print("+++++++++++++++++++++++++++++++")
'''
for game_id, game_dict in db['games'].items():
	print(game_id)
	stats_dict = build_stats()
	for player_id, game in game_dict['games'].items():
		#print(player_id)
		try:
			player_game = db['players'][player_id]['games'][game_id]
			#game_dict['games'][player_id] = player_game # For DEEP sanitization, but takes time.
			update_stats(stats_dict, player_game)
		except KeyError:
			print('KeyError')
			del game_dict['games'][player_id]
	game_dict['stats'] = stats_dict