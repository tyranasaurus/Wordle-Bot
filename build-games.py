from replit import db
import re

def add_game_stats(stats, game):
	if game['win']:
		stats['won'] += 1
		stats['scores_dict'][str(game['score'])] += 1
	else:
		stats['lost'] += 1
		stats['scores_dict']['X'] += 1
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
		'scores_dict': {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0, 'X': 0},
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

def build_game_dict():
	return {
		'stats': build_stats()
	}

try:
	del db['games']
except:
	print("No database")
db['games'] = {}

for player_id, player in db['players'].items():
	try:
		print(player['name'])
	except KeyError:
		print(player)
		input()
	player['stats'] = build_stats()
	remove_ids = []
	for game_id, player_game in player['games'].items():
		if not player_game:
			remove_ids.append(game_id)
			continue
		#print(game_id)
		try:
			game_dict = db['games'][game_id]
			#print('old')
		except KeyError:
			game_dict = build_game_dict()
			#print('new')
		error = False
		rows = player_game['rows']
		guesses = player_game['guesses']
		max_turns = player_game['max turns']
		print('r', rows)
		if (guesses < 1 or guesses > max_turns):
			print('guesses out of range')
			error = True
		try:
			found = re.findall("\n((?:\n([🟩🟧🟨🟦⬛⬜]{5})){"+str(guesses)+"})([^\n🟩🟧🟨🟦⬛⬜]+.*|\n[^🟩🟧🟨🟦⬛⬜]+.*|)$", rows)
			if not found:
				print("doesn't fit regex")
				error = True
		except TypeError:
			error = True
		if error:
			remove_ids.append(game_id)
			continue
		rows = found[0][0]
		player_game['rows'] = rows
		add_game_stats(player['stats'], player_game)
		add_game_stats(game_dict['stats'], player_game)
		db['games'][game_id] = game_dict
	for game_id in remove_ids:
		del player['games'][game_id]
	db['players'][player_id] = player
print('done')
	
		