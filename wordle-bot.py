import os
import discord
from dotenv import load_dotenv

from discord.ext import commands

import constants
import keep_alive
import logging
import DiscordUtils
import asyncio

import re

from replit import db

from collections import defaultdict

logging.basicConfig(level=logging.INFO)

async def get_prefix(bot, message):
	guild = message.guild
	guild_id = str(guild.id)
	if guild:
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

def build_game(score, max_turns, rows):
	game = {}
	if score == 'X':
		game['score'] = max_turns + constants.PENALTY
		game['guesses'] = max_turns
		game['win'] = False
	else:
		game['score'] = int(score)
		game['guesses'] = int(score)
		game['win'] = True
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

def build_player(name):
	return {
		'games': {},
		'name': name,
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

def create_help_embed(ctx):
	guild_id = str(ctx.guild.id)
	prefix = db['guilds'][guild_id]['prefix']
	author=ctx.author
	help_embed = discord.Embed(title='WORDLE BOT HELP', author=author, color=constants.COLOR1)
	help_embed.description = 'List of all the commands for the bot and what they do, along with other information.\nDISCLAIMER: this bot is not robust and is not meant to check inputs for correctness, so don\'t treat it as such. Instead, just post your scores and have fun!'
	help_embed.add_field(name='Submit New Score', value='-Every day, go to https://www.powerlanguage.co.uk/wordle/ and play Wordle!\n-Once done, click share score, copy to clipboard, and paste it into a channel, and the bot will log your score', inline=False)
	help_embed.add_field(name=prefix+'lb or '+prefix+'leaderboard', value='Displays the leaderboard for this server. Your wordle stats are synced across servers!', inline=False)
	help_embed.add_field(name=prefix+'lbs or '+prefix+'simple', value='Displays a more compact leaderboard for this server.', inline=False)
	help_embed.add_field(name=prefix+'stats', value='Displays your individual wordle stats', inline=False)
	help_embed.add_field(name=prefix+'games id1 id2 ...', value='Displays your wordle games. You can specify specific game ids, or leave it blank to display them all.', inline=False)
	help_embed.add_field(name=prefix+'prefix [new_prefix]', value="Changes Wordle bot's command prefix. You must have admin privileges in your server", inline=False)
	help_embed.add_field(name='REACTION GUIDE', value="✅ - Score processed\n👯 - You've already submitted this wordle!\n❓ - The bot doesn't know who you are, so you can't use this command! Send a wordle game first to get started!\n❌📂😞 - Game data not stored, sorry!\n♻️ - updated stored game in bot (won't affect stats)", inline=False)
	help_embed.add_field(name='Add the bot to your own server!', value='On a computer, click on the bot and hit \'Add to Server\' to use it in another server!', inline=False)
	help_embed.set_author(name=author, icon_url=author.avatar_url)
	help_embed.add_field(name=prefix+'info', value='Contains new and planned features, announcements, and other general information!', inline=False)
	help_embed.add_field(name='Join the Wordle Bot Community Server!', value='https://discord.gg/B492ArRmCQ. Join to report bugs, suggest features, get help, and witness and assist with bot development!', inline=False)
	return help_embed

def create_info_embed(ctx):
	author=ctx.author
	info_embed = discord.Embed(title='WORDLE BOT INFO', author=author, color=constants.COLOR1)
	info_embed.description = 'Contains new updates, planned features, announcements, and more! This bot is created by Tyranasaurus#3952. Message them with any questions!'
	info_embed.add_field(name='New in version 2.2', value='Bot responds to mentions, and command prefixes can be changed.', inline=False)
	info_embed.add_field(name='Planned Features', value='-Allow deletion of game with specific id\n-ability to see individual stats/games of someone other than yourself\n-Modify leaderboard to be based on a recency weightage.\n-Notification system reminding you to play your daily game.', inline=False)
	info_embed.add_field(name='Join the Wordle Bot Community Server!', value='https://discord.gg/B492ArRmCQ. Join to report bugs, suggest features, get help, and witness and assist with bot development!', inline=False)
	info_embed.set_author(name=author, icon_url=author.avatar_url)
	info_embed.set_footer(text = "Wordle Bot v2.2")
	return info_embed

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

@bot.command(name='stats',
             aliases=[],
             help=': Prints your statistics')
async def stats(ctx):
	author = ctx.author
	player_id = str(author.id)
	try:
		player = db['players'][player_id]
	except KeyError:
		#await ctx.send(embed = create_embed("You have no stored wordle games! Send a wordle game first to use this command!","", author, constants.COLOR2))
		await ctx.message.add_reaction('❓')
		return

	stats = player['stats']
	await ctx.send(embed=create_embed("", "Average score: " + str(stats['saverage']) + "\nWinrate: " + str(stats['winrate']) + "%\nGames Played: " + str(stats['played']) + "\nAverage 🟩: " + str(stats['gaverage']) + "\nAverage 🟨: " + str(stats['yaverage']), author, constants.COLOR1))
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
	info_embed = create_info_embed(ctx)
	await ctx.send(embed=info_embed)
	return

@bot.command(name='reset',
             aliases=[])
@commands.is_owner()
async def reset(ctx, *player_ids):
	message = ctx.message
	names=[]
	for player_id in player_ids:
		try:
			names.append(db['players'][player_id]['name'])
		except KeyError:
			continue
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
			for player_id in player_ids:
				del db['players'][player_id]
			await ctx.send(embed = create_embed("Done!", "", ctx.author, constants.COLOR1))
	return

@bot.command(name='prefix',
	         aliases=['change_prefix'],
             help=': Displays bot and feature info')
@commands.has_permissions(administrator=True)
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
	print('guild: ', guild.name)
	#invites = await guild.invites()
	#print(invites)
	channel = message.channel
	content = message.content
	if not re.search("^Wordle \d+ ([1-9]+\d*|X)/[1-9]+\d*[*\n🟩🟧🟨🟦⬛⬜]+", content):
		#print("Random Message")
		await bot.process_commands(message)
		return
	try:
		player = db['players'][player_id]
	except KeyError:
		player=build_player(author.name+"#"+author.discriminator)
	
	space_0 = content.find(' ')
	space_1 = content[space_0 + 1:].find(' ')
	rows = content[content.find('\n'):]
	game_id = int(content[space_0 + 1 : space_0 + 1 + space_1])
	if (str(game_id) in list(player['games'].keys()) and player['games'][str(game_id)]):
		await message.add_reaction('👯')
		return

	score = content[content.find('/') - 1]
	max_turns = int(content[content.find('/') + 1])
	game = build_game(score, max_turns, rows)
	if (str(game_id) in list(player['games'].keys()) and not player['games'][str(game_id)]):
		await message.add_reaction('♻️')
	else:
		update_stats(player['stats'], game)
		await message.add_reaction('✅')
	player['games'][str(game_id)] = game
	db['players'][player_id] = player
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

@bot.command(name='lbs',
             aliases=['simple'],
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

@bot.command(name='lb',
             aliases=['leaderboard'],
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

async def display_games(ctx, player, games):
	title = player['name'].upper() + " WORDLES"
	description = "Use the arrows at the bottom to navigate through the pages."
	embeds = []
	numPages = (len(games)-1)//constants.games_per_page + 1

	for gameIndex in range(0, len(games)):
		pageIndex=gameIndex//constants.games_per_page
		if gameIndex % constants.games_per_page == 0:
			embeds.append(discord.Embed(title=title+" (Page "+str(pageIndex+1)+"/"+str(numPages)+")", description=description, author=ctx.author, color=constants.GREEN))
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

@bot.command(name='games',
             aliases=['game'],
             help='Displays your stats for a specific game')
async def games(ctx, *game_ids):
	guild = ctx.guild
	author = ctx.author
	player_id = str(author.id)

	try:
		player = db['players'][player_id]
	except KeyError:
		#await ctx.send(embed = create_embed("You have no stored wordle games! Send a wordle game first to use this command!","", author, constants.COLOR2))
		await ctx.message.add_reaction('❓')
		return
	relevant_games = {}
	for game_id in game_ids:
		try:
			game = player['games'][game_id]
			relevant_games[game_id] = game
		except KeyError:
			continue
	if not relevant_games:
		relevant_games = player['games']
	await display_games(ctx, player, sorted(list(relevant_games.items()), key = lambda x: int(x[0])*-1))
	return




keep_alive.keep_alive()

bot.run(TOKEN)
