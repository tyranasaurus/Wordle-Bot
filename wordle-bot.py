import os
import discord
from dotenv import load_dotenv

from discord.ext import commands

import constants
import keep_alive
import logging
import DiscordUtils
import asyncio
import time

import re

from replit import db

from collections import defaultdict

logging.basicConfig(level=logging.INFO)

async def get_prefix(bot, message):
	guild = message.guild
	if guild:
		guild_id = str(guild.id)
		try:
			db['guilds'][guild_id]
		except KeyError:
			db['guilds'][guild_id] = {'name': guild.name, 'prefix': constants.default_prefix}
			print(db['guilds'][guild_id])
		prefix = db['guilds'][guild_id]['prefix']
	else:
		prefix = constants.default_prefix
	return commands.when_mentioned_or(*prefix)(bot, message)

intents = discord.Intents.default()
intents.members = True
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix=get_prefix, case_insensitive = True, strip_after_prefix = True, intents=intents)
bot.remove_command('help')

global roles
global active_authors
global messages_map
roles = []
active_authors = []
messages_map = {}

def build_game(score, guesses, win, max_turns, rows):
	game = {}
	game['score'] = score
	game['guesses'] = guesses
	game['win'] = win
	game['max turns'] = max_turns
	game['rows'] = rows
	green = 0
	yellow = 0
	black = 0
	for char in rows:
		if char == '🟩' or char == '🟧':
			green += 1
		elif char == '🟨' or char == '🟦':
			yellow += 1
		elif char == '⬛' or char == '⬜':
			black += 1
	game['green'] = green
	game['yellow'] = yellow
	game['black'] = black
	return game

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

def remove_game(player_id, game_id):
	print('removing')
	try:
		print('trying')
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
	

def remove_game_stats(stats, game):
	stats['played'] -= 1
	if game['win']:
		stats['won'] -= 1
		stats['scores_dict'][str(game['score'])] -= 1
	else:
		stats['lost'] -= 1
		stats['scores_dict']['X'] -= 1
	stats['score'] -= game['score']
	stats['guesses'] -= game['guesses']
	stats['winrate'] = int(round(stats['won'] / stats['played'], 2)*100)
	stats['green'] -= game['green']
	stats['yellow'] -= game['yellow']
	stats['black'] -= game['black']
	stats['saverage'] = round(stats['score'] / stats['played'], 2)
	stats['gaverage'] = round(stats['green'] / stats['guesses'] , 2)
	stats['yaverage'] = round(stats['yellow'] / stats['guesses'], 2)
	stats['baverage'] = round(stats['black'] / stats['guesses'], 2)
	return

def build_player(name):
	return {
		'games': {},
		'name': name,
		'subscribed': True,
		'stats': build_stats()
	}

def build_game_dict():
	return {
		'stats': build_stats()
	}


def create_embed(message, sub_message, author, color):
    embed = discord.Embed(title=message, description=sub_message, color=color)
    if author:
        if author == 'bot':
            author = bot.user
        embed.set_author(name=author, icon_url=author.avatar_url)
    #print(len(embed))
    return embed

async def sendDm(user_id, content = None, embed = None):
    user = await bot.fetch_user(user_id)
    await user.send(content = content, embed = embed)

def create_help_embed(ctx):
	if ctx.guild:
		guild_id = str(ctx.guild.id)
		prefix = db['guilds'][guild_id]['prefix']
	else:
		prefix = constants.default_prefix
	author=ctx.author
	help_embed = discord.Embed(title='WORDLE BOT HELP', author=author, color=constants.COLOR1)
	help_embed.description = 'List of all the commands for the bot and what they do, along with other information.\nDISCLAIMER: this bot is not robust and is not meant to check inputs for correctness, so don\'t treat it as such. Instead, just post your scores and have fun!'
	help_embed.add_field(name='Submit New Score', value='-Every day, go to https://www.powerlanguage.co.uk/wordle/ and play Wordle!\n-Once done, click share score, copy to clipboard, and paste it into a channel, and the bot will log your score', inline=False)
	help_embed.add_field(name=prefix+'lb or '+prefix+'leaderboard', value='Displays a compact leaderboard for this server. Your wordle stats are synced across servers!', inline=False)
	help_embed.add_field(name=prefix+'lbd or '+prefix+'detailed', value='Displays a more detailed leaderboard for this server.', inline=False)
	help_embed.add_field(name=prefix+'lbw or '+prefix+'weighted', value='Displays the (currently experimental) weighted leaderboard for this server.', inline=False)
	help_embed.add_field(name=prefix+'games id1 id2 ...', value='Displays overall statistics for wordle games, including average score and winrate. You can specify specific game ids, or leave it blank to display them all.', inline=False)
	help_embed.add_field(name=prefix+'player [@member]', value="Displays your or another member's wordle stats", inline=False)
	help_embed.add_field(name=prefix+'archive id1 id2 ...', value='Displays your wordle games. You can specify specific game ids, or leave it blank to display them all.', inline=False)
	help_embed.add_field(name=prefix+'prefix [new_prefix]', value="Changes Wordle bot's command prefix. You must have admin privileges in your server", inline=False)
	help_embed.add_field(name='REACTION GUIDE', value="✅ - Score processed\n👯 - You've already submitted this wordle!\n❓ - The bot doesn't know who you are, so you can't use this command! Send a wordle game first to get started!\n❌📂😞 - Game data not stored, sorry!\n♻️ - updated stored game in bot (won't affect stats)", inline=False)
	help_embed.add_field(name='Add the bot to your own server!', value='On a computer, click on the bot and hit \'Add to Server\' to use it in another server!', inline=False)
	help_embed.set_author(name=author, icon_url=author.avatar_url)
	help_embed.add_field(name=prefix+'info', value='Contains new and planned features, announcements, and other general information!', inline=False)
	help_embed.add_field(name='Join the Wordle Bot Community Server!', value='https://discord.gg/B492ArRmCQ. Join to report bugs, suggest features, get help, and witness and assist with bot development!', inline=False)
	return help_embed

async def create_announce_embed():
	me = await bot.fetch_user(constants.owner_id)
	announce_embed = discord.Embed(title='WORDLE BOT v3.1.1!', author=me, color=constants.COLOR1)
	announce_embed.set_footer(text = "This message was automatically sent by Wordle Bot. If you would like to unsubscribe from future announcements, send me 'STOP'")
	announce_embed.description = 'New updates to bot structure!'
	announce_embed.add_field(name="What's new in Wordle Bot v3.0?", value="- Sanitized Archive\n- Re-calibrated stats\n- A cool new player statistics histogram (use !player) to view\n- an experimental version of the new leaderboard (use !lbw to see). Note: bot may be slow in producing leaderboard at the moment.\n- More robust checks for valid inputs.\n- the default leaderboard is now the simple one, use !lbd for the detailed view.", inline=False)
	announce_embed.add_field(name="What's in the works?", value="- A new scoring system that makes the leaderboard more dynamic!\n- An optional notification system to remind you to play your wordle game daily\n- Ability to undo the last submitted wordle in event of a mistake.\n- Even more robust checks for valid inputs.", inline=False)
	announce_embed.add_field(name='Add the bot to your own server!', value='On a computer, click on the bot and hit \'Add to Server\' to use it in another server! You must have admin privileges to do so. Scores sync across servers!', inline=False)
	announce_embed.add_field(name='Have suggestions/bugs? Join the Wordle Bot Community Server!', value='https://discord.gg/B492ArRmCQ. Join to report bugs, suggest features, get help, and witness and assist with bot development!', inline=False)
	announce_embed.set_author(name=me.name+"#"+me.discriminator, icon_url=me.avatar_url)
	return announce_embed

@bot.event
async def on_ready():
	print(f'{bot.user.name} has connected to Discord!')
	await bot.change_presence(activity=discord.Streaming(name="Wordle", url='https://www.powerlanguage.co.uk/wordle'))
	await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!help"))
	print("I'm in "+str(len(bot.guilds))+" guilds!")

@bot.check
def check_author(ctx):
	return True
	global active_authors
	if ctx.author in active_authors:
		return False
	else:
		active_authors.append(ctx.author)
		return True

@bot.after_invoke
async def deactivate_author(ctx):
	global active_authors
	try:
		active_authors.remove(ctx.author)
	except ValueError:
		print("ValueError")
		pass

async def make_histogram(played, scores_dict):
	print(played)
	print(scores_dict)
	histogram=''
	num_per_box = max(list(scores_dict.values())) / constants.histogram_width
	histogram += '1️⃣' + int(round(scores_dict['1']/num_per_box))*'🟩'+'\n'
	histogram += '2️⃣' + int(round(scores_dict['2']/num_per_box))*'🟩'+'\n'
	histogram += '3️⃣' + int(round(scores_dict['3']/num_per_box))*'🟩'+'\n'
	histogram += '4️⃣' + int(round(scores_dict['4']/num_per_box))*'🟩'+'\n'
	histogram += '5️⃣' + int(round(scores_dict['5']/num_per_box))*'🟩'+'\n'
	histogram += '6️⃣' + int(round(scores_dict['6']/num_per_box))*'🟩'+'\n'
	histogram += '💀' + int(round(scores_dict['X']/num_per_box))*'🟩'
	return histogram

@bot.command(name='player',
             aliases=[],
             help=": prints your or another player's statistics")
async def stats(ctx, member: discord.Member = None):
	player = member or ctx.author
	player_id = str(player.id)
	try:
		player_dict = db['players'][player_id]
	except KeyError:
		#await ctx.send(embed = create_embed("You have no stored wordle games! Send a wordle game first to use this command!","", author, constants.COLOR2))
		await ctx.message.add_reaction('❓')
		return

	stats = player_dict['stats']
	await ctx.send(embed=create_embed("", "Average score: " + str(stats['saverage']) + "\nWinrate: " + str(stats['winrate']) + "%\nGames Played: " + str(stats['played']) + "\nAverage 🟩: " + str(stats['gaverage']) + "\nAverage 🟨: " + str(stats['yaverage'])+'\n\n'+await make_histogram(stats['played'], stats['scores_dict']), player, constants.COLOR1))
	return

@bot.command(
	name='help',
	aliases=[],
	help=
	'provides bot help'
)
async def help(ctx):
	author = ctx.author
	help_embed = create_help_embed(ctx)
	await ctx.send(embed=help_embed)

@bot.command(name='info',
             aliases=[],
             help=': Displays bot and feature info')
async def info(ctx):
	announce_embed = await create_announce_embed()
	announce_embed.set_footer(text = "")
	await ctx.send(embed=announce_embed)
	return

@bot.command(name='reset',
             aliases=[])
@commands.is_owner()
async def reset(ctx, *player_ids):
	message = ctx.message
	valid = []
	names=[]
	for player_id in player_ids:
		try:
			names.append(db['players'][player_id]['name'])
		except KeyError:
			continue
		valid.append(player_id)
	response = await ctx.send(embed = create_embed("Are you sure you want to do this?", "This will delete the databases for the users: "+str(names), ctx.author, constants.COLOR2))
	await response.add_reaction('✅')
	await response.add_reaction('❌')
	def check(reaction, user):
		return user == message.author and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')
	try:
		reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
	except asyncio.TimeoutError:
		await response.add_reaction('⌛')
	else:
		if str(reaction.emoji) == '✅':
			for player_id in valid:
				game_ids = list(db['players'][player_id]['games'].keys())
				if not game_ids:
					print('last game')
					del db['players'][player_id]
				for game_id in game_ids:
					remove_game(player_id, game_id)
				#await sendDm(int(player_id), embed = create_embed("Your Wordle Scores have been reset.", "You may resend any scores you would like to keep.", bot.user, constants.COLOR2))
			await ctx.send(embed = create_embed("Done!", "", ctx.author, constants.COLOR1))
	return

@bot.command(name='remove',
             aliases=[])
@commands.is_owner()
async def remove(ctx, player_id, *game_ids):
	message = ctx.message
	try:
		name = db['players'][player_id]['name']
	except KeyError:
		await message.add_reaction('❌')
		return
	valid = []
	for game_id in game_ids:
		try:
			game = db['players'][player_id]['games'][game_id]
		except KeyError:
			continue
		valid.append(game_id)
	if not valid:
		await message.add_reaction('❌')
		return
	response = await ctx.send(embed = create_embed("Are you sure you want to do this?", "This will delete the games "+str(game_ids)+" for the users: "+name, ctx.author, constants.COLOR2))
	await response.add_reaction('✅')
	await response.add_reaction('❌')
	def check(reaction, user):
		return user == message.author and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')
	try:
		reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
	except asyncio.TimeoutError:
		await response.add_reaction('⌛')
	else:
		if str(reaction.emoji) == '✅':
			for game_id in valid:
				print('remove')
				remove_game(player_id, game_id)
			#await sendDm(int(player_id), embed = create_embed("Your Wordle Scores for Wordle numbers "+str(valid)+" have been removed.", "You may resend any scores you would like to keep.", bot.user, constants.COLOR2))
			await ctx.send(embed = create_embed("Done!", "", ctx.author, constants.COLOR1))
	return


@bot.command(name='announce',
             aliases=[])
@commands.is_owner()
async def announce(ctx):
	announce_embed = await create_announce_embed()
	count = 0
	for player_id, player_dict in db['players'].items():
		print(player_dict['name'])
		try:
			subscribed = player_dict['subscribed']
		except KeyError:
			player_dict['subscribed'] = True
			subscribed = True
		if not player_dict['subscribed']:
			continue
		count += 1
		if count < 58:
			continue
		print(count)
		#await sendDm(int(player_id), embed = announce_embed)
		time.sleep(1)
	return

@bot.command(name='prefix',
	         aliases=['change_prefix'],
             help=': Displays bot and feature info')
@commands.has_guild_permissions(administrator=True)
async def prefix(ctx, prefix):
	guild = ctx.guild
	guild_id = str(guild.id)
	db['guilds'][guild_id]['prefix'] = prefix.strip()
	await ctx.message.add_reaction('✅')
	return
'''
@bot.command(name='channel',
             aliases=['set_channel'])
@commands.has_permissions(administrator=True)
async def prefix(ctx, channel):
	guild = ctx.guild
	guild_id = str(guild.id)
	db['guilds'][guild_id]['prefix'] = prefix.strip()
	await ctx.message.add_reaction('✅')
	return
'''
@bot.event
async def on_message(message):
	author = message.author
	player_id = str(author.id)
	guild = message.guild
	#print('guild: ', guild.name)
	#invites = await guild.invites()
	#print(invites)
	channel = message.channel
	content = message.content
	if not guild:
		if message.content.strip().upper() == 'STOP' or message.content.strip().upper() == 'UNSUBSCRIBE':
			db['players'][player_id]['subscribed'] = False
			await message.channel.send(embed = create_embed("You've been unsubscribed from Wordle Bot Announcements", "We're sorry to see you go! You can always resubscribe with 'start' or 'subscribe'", author, constants.COLOR2))
			return
		if message.content.strip().upper() == 'START' or message.content.strip().upper() == 'SUBSCRIBE':
			db['players'][player_id]['subscribed'] = True
			await message.channel.send(embed = create_embed("You've been subscribed to Wordle Bot Announcements!", "You can always unsubscribe with 'stop' or 'unsubscribe'", author, constants.COLOR1))
			return
	print(str(content))
	header_fmt = re.compile("^Wordle ([1-9]+\d*) ([1-9]+\d*|X)/([1-9]+\d*)\*?(.*)", re.DOTALL)
	header = re.findall(header_fmt, content)
	if not header:
		print("Random Message")
		await bot.process_commands(message)
		return
	try:
		player = db['players'][player_id]
	except KeyError:
		player=build_player(author.name+"#"+author.discriminator)
	print("Wordle Message")
	header = header[0]
	game_id = str(header[0])
	if (game_id in list(player['games'].keys())):
		await message.add_reaction('👯')
		return
	error = False
	score = str(header[1])
	max_turns = int(header[2])
	if score == 'X':
		score = max_turns + constants.PENALTY
		guesses = max_turns
		win = False
	else:
		score = int(score)
		guesses = score
		win = True
	if (guesses < 1 or guesses > max_turns):
		print('guesses out of range')
		error = True
	rows = header[3]
	print('r', rows)
	print(guesses)
	found = re.findall("\n((?:\n([🟩🟧🟨🟦⬛⬜]{5})){"+str(guesses)+"})([^\n🟩🟧🟨🟦⬛⬜]+.*|\n[^🟩🟧🟨🟦⬛⬜]+.*|)$", rows, re.DOTALL)
	if not found:
		print("doesn't fit regex")
		error = True
	print(found)
	if error:
		await message.add_reaction('❌')
		return
	
	try:
		game_dict = db['games'][str(game_id)]
	except KeyError:
		game_dict = build_game_dict()

	rows = found[0][0]
	game = build_game(score, guesses, win, max_turns, rows)
	add_game_stats(player['stats'], game)
	add_game_stats(game_dict['stats'], game)
	player['games'][str(game_id)] = game
	db['players'][player_id] = player
	db['games'][str(game_id)] = game_dict
	await message.add_reaction('✅')
	return

async def getSortedPlayers(ctx):
	guild = ctx.guild
	author = ctx.author
	guild_players = []
	guild_members = guild.members
	member_ids = []
	for member in guild_members:
		member_ids.append(str(member.id))
	for player_id, player in db['players'].items():
		if player_id not in member_ids:
			continue
		guild_players.append(player)
	if not len(guild_players):
		await ctx.send(embed=create_embed("No wordle games have been added yet! Send some game results to get started!", "", author, constants.COLOR2))
		return
	return sorted(guild_players, key = lambda x: (x['stats']['saverage'], x['stats']['winrate']*-1, x['stats']['played']*-1, x['stats']['gaverage']*-1, x['stats']['yaverage']*-1))

async def getSortedbyWeightPlayers(ctx):
	guild = ctx.guild
	author = ctx.author
	guild_players = []
	guild_members = guild.members
	member_ids = []
	for member in guild_members:
		member_ids.append(str(member.id))
	for player_id, player in db['players'].items():
		if player_id not in member_ids:
			continue
		guild_players.append(player)
	if not len(guild_players):
		await ctx.send(embed=create_embed("No wordle games have been added yet! Send some game results to get started!", "", author, constants.COLOR2))
		return
	for player in guild_players:
		player_games = player['games']
		last = max(player_games.keys(), key=int)
		print(last)
		first = last - constants.ewma_window
		ewma = 0
		a = 2/(constants.ewma_window+1)
		try:
			ewma = player_games[str(first)]['score']
		except KeyError:
			try:
				ewma = db['games'][str(first)]['stats']['score']
			except KeyError:
				ewma = 4 #Fix this to be overall avg or smthn
		for id in range(first+1, last+1):
			try:
				ewma = a*player_games[str(id)]['score']+(1-a)*ewma
			except KeyError:
				try:
					ewma = a*db['games'][str(first)]['stats']['score']+(1-a)*ewma
				except KeyError:
					ewma = a*4+(1-a)*ewma #Fix this to be overall avg or smthn
		player['stats']['ewma'] = ewma
	return sorted(guild_players, key = lambda x: (x['stats']['ewma'], x['stats']['saverage'], x['stats']['winrate']*-1, x['stats']['played']*-1, x['stats']['gaverage']*-1, x['stats']['yaverage']*-1))

@bot.command(name='lb',
             aliases=['leaderboard'],
             help=': Displays your statistics')
async def lbs(ctx):
	author = ctx.author
	sortedPlayers = await getSortedPlayers(ctx)
	title = "Wordle Leaderboard"
	description = ""
	for playerIndex in range(0, len(sortedPlayers)):
		player = sortedPlayers[playerIndex]
		stats = player['stats']
		description += str(playerIndex+1)+'. '+player['name']+' - ' + str(stats['saverage']) + '\n'
	await ctx.send(embed=create_embed(title, description[:-1], None, constants.COLOR1))
	print("hello")
	return

@bot.command(name='lbw',
             aliases=['weighted'],
             help=': Displays your statistics')
async def lbn(ctx):
	author = ctx.author
	sortedPlayers = await getSortedbyWeightPlayers(ctx)
	title = "Wordle Leaderboard"
	description = ""
	for playerIndex in range(0, len(sortedPlayers)):
		player = sortedPlayers[playerIndex]
		stats = player['stats']
		description += str(playerIndex+1)+'. '+player['name']+' - ' + str(stats['ewma']) + '\n'
	await ctx.send(embed=create_embed(title, description[:-1], None, constants.COLOR1))
	print("hello")
	return

@bot.command(name='lbd',
             aliases=['detailed'],
             help='Displays the wordle leaderboard')
async def lb(ctx):
	author = ctx.author
	sortedPlayers = await getSortedPlayers(ctx)
	title = "Wordle Leaderboard"
	description = "Use the arrows at the bottom to navigate through the pages."
	embeds = []
	numPages = (len(sortedPlayers)-1)//constants.players_per_page + 1
	
	for playerIndex in range(0, len(sortedPlayers)):
		pageIndex=playerIndex//constants.players_per_page
		if playerIndex % constants.players_per_page == 0:
			embeds.append(discord.Embed(title=title+" (Page "+str(pageIndex+1)+"/"+str(numPages)+")", description=description, author=author, color=constants.GREEN))
		player = sortedPlayers[playerIndex]
		stats = player['stats']
		embeds[pageIndex].add_field(name=str(playerIndex+1)+'. '+player['name'], value="Average score: " + str(stats['saverage']) + "\nWinrate: " + str(stats['winrate']) + "%\nGames Played: " + str(stats['played']) + "\nAverage 🟩: " + str(stats['gaverage']) + "\nAverage 🟨: " + str(stats['yaverage']), inline = False)
	paginator = DiscordUtils.Pagination.CustomEmbedPaginator(ctx, timeout = constants.TIMEOUT/2, auto_footer=True, remove_reactions=True)
	paginator.add_reaction('⏮️', "first")
	paginator.add_reaction('⏪', "back")
	paginator.add_reaction('🔐', "lock")
	paginator.add_reaction('⏩', "next")
	paginator.add_reaction('⏭️', "last")
	#print(len(embeds))
	await paginator.run(embeds)
	return

async def display_archive(ctx, player, games):
	player_dict = db['players'][str(player.id)]
	title = player_dict['name'] + " Wordles"
	description = "Use the arrows at the bottom to navigate through the pages."
	embeds = []
	numPages = (len(games)-1)//constants.archives_per_page + 1

	for gameIndex in range(0, len(games)):
		pageIndex=gameIndex//constants.archives_per_page
		if gameIndex % constants.archives_per_page == 0:
			embeds.append(discord.Embed(title=title+" (Page "+str(pageIndex+1)+"/"+str(numPages)+")", description=description, author=player, color=constants.GREEN))
		game_id, game = games[gameIndex]
		if game:
			if game['win']:
				score = str(game['score'])
			else:
				score = 'X'
			name = 'Wordle '+str(game_id)+' ' + str(score) + '/'+str(game['max turns'])
			val = game['rows']
		else:
			name = 'Wordle '+str(game_id)
			val = "❌📂😞"
		embeds[pageIndex].add_field(name=name, value=val, inline = True)
	paginator = DiscordUtils.Pagination.CustomEmbedPaginator(ctx, timeout = constants.TIMEOUT/2, auto_footer=True, remove_reactions=True)
	paginator.add_reaction('⏮️', "first")
	paginator.add_reaction('⏪', "back")
	paginator.add_reaction('🔐', "lock")
	paginator.add_reaction('⏩', "next")
	paginator.add_reaction('⏭️', "last")
	#print(len(embeds))
	await paginator.run(embeds)
	return

@bot.command(name='archive',
             aliases=[],
             help='Displays your stats for specific game(s)')
async def games(ctx, *game_ids):
	player = ctx.author
	player_id = str(player.id)

	try:
		player_dict = db['players'][player_id]
	except KeyError:
		#await ctx.send(embed = create_embed("You have no stored wordle games! Send a wordle game first to use this command!","", author, constants.COLOR2))
		await ctx.message.add_reaction('❓')
		return
	relevant_games = {}
	for game_id in game_ids:
		try:
			game = player_dict['games'][game_id]
			relevant_games[game_id] = game
		except KeyError:
			continue
	if not relevant_games:
		relevant_games = player_dict['games']
	await display_archive(ctx, player, sorted(list(relevant_games.items()), key = lambda x: int(x[0])*-1))
	return

async def display_games(ctx, player, games):
	player_dict = db['players'][str(player.id)]
	title = "Wordle Game Stats"
	description = "Use the arrows at the bottom to navigate through the pages."
	embeds = []
	numPages = (len(games)-1)//constants.games_per_page + 1

	for gameIndex in range(0, len(games)):
		pageIndex=gameIndex//constants.games_per_page
		if gameIndex % constants.games_per_page == 0:
			embeds.append(discord.Embed(title=title+" (Page "+str(pageIndex+1)+"/"+str(numPages)+")", description=description, author=player, color=constants.GREEN))
		game_id, game = games[gameIndex]
		stats = game['stats']
		name = 'Wordle '+str(game_id)
		val = "Average score: " + str(stats['saverage']) + "\nWinrate: " + str(stats['winrate']) + "%\nGames Played: " + str(stats['played']) + "\nAverage 🟩: " + str(stats['gaverage']) + "\nAverage 🟨: " + str(stats['yaverage']) + '\n\n' + await make_histogram(stats['played'], stats['scores_dict'])
		embeds[pageIndex].add_field(name=name, value=val, inline = True)
	paginator = DiscordUtils.Pagination.CustomEmbedPaginator(ctx, timeout = constants.TIMEOUT/2, auto_footer=True, remove_reactions=True)
	paginator.add_reaction('⏮️', "first")
	paginator.add_reaction('⏪', "back")
	paginator.add_reaction('🔐', "lock")
	paginator.add_reaction('⏩', "next")
	paginator.add_reaction('⏭️', "last")
	#print(len(embeds))
	await paginator.run(embeds)
	return

@bot.command(name='game',
             aliases=['games'],
             help='Displays overall stats for specific games')
async def games(ctx, *game_ids):
	player = ctx.author
	player_id = str(player.id)

	relevant_games = {}
	for game_id in game_ids:
		try:
			game = db['games'][game_id]
			relevant_games[game_id] = game
		except KeyError:
			continue
	if not relevant_games:
		relevant_games = db['games']
	await display_games(ctx, player, sorted(list(relevant_games.items()), key = lambda x: int(x[0])*-1))
	return

keep_alive.keep_alive()

bot.run(TOKEN)
