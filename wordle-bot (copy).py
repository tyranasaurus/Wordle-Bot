import os
import discord
from dotenv import load_dotenv

from discord.ext import commands

import constants
import keep_alive
import asyncio
import datetime
import logging
import validators
import DiscordUtils

from replit import db

from collections import defaultdict

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.members = True
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')


global roles
global active_authors
global messages_map
roles = []
active_authors = []
messages_map = {}

class Game:
	def __init__(self, game_id, score, max_turns, rows):
		self.id = game_id
		self.score = score
		self.max_turns = max_turns
		self.rows = rows
	
		
		


def create_embed(message, sub_message, author, color):
    embed = discord.Embed(title=message, description=sub_message, color=color)
    if author:
        if author == 'bot':
            author = bot.user
        embed.set_author(name=author, icon_url=author.avatar_url)
    #print(len(embed))
    return embed

def create_help_embed(ctx):
	author=ctx.author
	help_embed = discord.Embed(title='WORDLE BOT HELP', author=author, color=constants.COLOR1)
	help_embed.description = 'List of all the commands for the bot and what they do.\nDISCLAIMER: this bot is not robust and is not meant to check inputs for correctness, so don\'t treat it as such. Instead, just post your scores and have fun!'
	help_embed.add_field(name='Submit New Score', value='-Every day, go to https://www.powerlanguage.co.uk/wordle/ and play Wordle!\n-Once done, click share score, copy to clipboard, and paste it into a channel, and the bot will log your score', inline=False)
	help_embed.add_field(name='!lb or !leaderboard', value='Displays the leaderboard for this server. Your wordle stats are synced across servers!', inline=False)
	help_embed.add_field(name='!lbs or !simple', value='Displays a more compact leaderboard for this server.', inline=False)
	help_embed.add_field(name='!stats', value='Displays your individual wordle stats', inline=False)
	help_embed.add_field(name='Add the bot to your own server!', value='On a computer, click on the bot and hit \'Add to Server\' to use it in another server!', inline=False)
	help_embed.set_author(name=author, icon_url=author.avatar_url)
	return help_embed

@bot.event
async def on_ready():
	print(f'{bot.user.name} has connected to Discord!')
	await bot.change_presence(activity=discord.Streaming(name="Wordle", url='https://www.powerlanguage.co.uk/wordle'))
	await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="For casual use only."))



def zero():
	return 0

@bot.check
def check_author(ctx):
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
	player = ctx.author
	player_id = str(player.id)
	player_dict = db[player_id]
	stats = player_dict['stats']
	await ctx.send(embed=create_embed("", "Average score: " + str(stats['score']) + "\nWinrate: " + str(stats['winrate']) + "%\nGames Played: " + str(stats['played']) + "\nAverage 🟩: " + str(stats['green']) + "\nAverage 🟨: " + str(stats['yellow']), player, constants.COLOR1))
	return

@bot.command(name='lbs',
             aliases=['simple'],
             help=': Displays your statistics')
async def lbs(ctx):
	guild = ctx.guild
	author = ctx.author
	guild_players = []
	guild_members = guild.members
	member_ids = []
	for member in guild_members:
		member_ids.append(str(member.id))
	for player_id, player_dict in db.items():
		if player_id not in member_ids:
			continue
		guild_players.append(player_dict['stats'])
	if not len(guild_players):
		await ctx.send(embed=create_embed("No wordle games have been added yet! Send some game results to get started!", "", author, constants.COLOR2))
		return
	
	sortedPlayers = sorted(guild_players, key = lambda x: (x['score'], x['winrate']*-1, x['played']*-1, x['green']*-1, x['yellow']*-1))
	title = "Wordle Leaderboard"
	description = ""
	embeds = []
	numPages = (len(sortedPlayers)-1)//constants.players_per_page + 1
	desc = ""
	for playerIndex in range(0, len(sortedPlayers)):
		stats = sortedPlayers[playerIndex]
		player = stats['player']
		description += str(playerIndex+1)+'. '+player+' - ' + str(stats['score']) + '\n'
	await ctx.send(embed=create_embed(title, description[:-1], None, constants.COLOR1))
	return

@bot.command(
	name='help',
	aliases=['info'],
	help=
	'provides bot help'
)
async def help(ctx):
	author = ctx.author
	help_embed = create_help_embed(ctx)
	await ctx.send(embed=help_embed)

@bot.event
async def on_message(message):
	player = message.author
	player_id = str(player.id)
	guild = message.guild
	print('guild: ', guild.name)
	#invites = await guild.invites()
	#print(invites)
	channel = message.channel
	content = message.content
	if not (content[0:7] == 'Wordle '):
		#print("Random Message")
		await bot.process_commands(message)
		return
	try:
		player_dict = db[player_id]
	except KeyError:
		player_dict=defaultdict(zero)
	#print(player_dict)
	#print(content)
	turns = content[content.find('/') - 1]
	green = 0
	yellow = 0
	black = 0
	space_0 = content.find(' ')
	space_1 = content[space_0 + 1:].find(' ')
	game_id = int(content[space_0 + 1 : space_0 + 1 + space_1])
	if player_dict['game_ids'] == 0:
		player_dict['game_ids'] = []
	if game_id in player_dict['game_ids']:
		await message.add_reaction('👯')
		return
	else:
		player_dict['game_ids'].append(game_id)
	for char in content:
		if char == '🟩' or char == '🟧':
			green += 1
		elif char == '🟨' or char == '🟦':
			yellow += 1
		elif char == '⬛' or char == '⬜':
			black += 1
	player_dict['won']
	player_dict['lost']
	if turns == 'X':
		player_dict['lost'] += 1
		player_dict['turns'] += int(content[content.find('/') + 1]) + constants.penalty
		player_dict['rows'] += int(content[content.find('/') + 1])
	elif (int(turns) > 0 and int(turns) <= int(content[content.find('/') + 1])):
		player_dict['won'] += 1
		player_dict['turns'] += int(turns)
		player_dict['rows'] += int(turns)
	else:
		#print('Not a valid wordle message')
		return
	player_dict['green'] += green
	player_dict['yellow'] += yellow
	player_dict['black'] += black
	won = player_dict['won']
	lost = player_dict['lost']
	played = won + lost
	score = round(player_dict['turns'] / played, 2)
	winrate = int(round(won / played, 2) * 100)
	rows = player_dict['rows']
	green = round(player_dict['green'] / rows, 2)
	yellow = round(player_dict['yellow'] / rows, 2)
	stats = {'player': player.name+"#"+player.discriminator, 'score': score, 'played': played, 'winrate': winrate, 'green':green, 'yellow':yellow}
	player_dict['stats'] = stats
	db[player_id] = player_dict
	#print(player_dict)
	await message.add_reaction('✅')
	return

@bot.command(name='lb',
             aliases=['leaderboard'],
             help='Displays the wordle leaderboard')
async def lb(ctx):
	guild = ctx.guild
	author = ctx.author
	guild_players = []
	guild_members = guild.members
	member_ids = []
	for member in guild_members:
		member_ids.append(str(member.id))
	for player_id, player_dict in db.items():
		if player_id not in member_ids:
			continue
		guild_players.append(player_dict['stats'])
	if not len(guild_players):
		await ctx.send(embed=create_embed("No wordle games have been added yet! Send some game results to get started!", "", author, constants.COLOR2))
		return
	
	sortedPlayers = sorted(guild_players, key = lambda x: (x['score'], x['winrate']*-1, x['played']*-1, x['green']*-1, x['yellow']*-1))
	title = "Wordle Leaderboard"
	description = "Use the arrows at the bottom to navigate through the pages."
	embeds = []
	numPages = (len(sortedPlayers)-1)//constants.players_per_page + 1
	
	for playerIndex in range(0, len(sortedPlayers)):
		pageIndex=playerIndex//constants.players_per_page
		if playerIndex % constants.players_per_page == 0:
			embeds.append(discord.Embed(title=title+" (Page "+str(pageIndex+1)+"/"+str(numPages)+")", description=description, author=author, color=constants.GREEN))
		stats = sortedPlayers[playerIndex]
		player = stats['player']
		embeds[pageIndex].add_field(name=str(playerIndex+1)+'. '+player, value="Average score: " + str(stats['score']) + "\nWinrate: " + str(stats['winrate']) + "%\nGames Played: " + str(stats['played']) + "\nAverage 🟩: " + str(stats['green']) + "\nAverage 🟨: " + str(stats['yellow']), inline = False)
	paginator = DiscordUtils.Pagination.CustomEmbedPaginator(ctx, timeout = constants.TIMEOUT/2, auto_footer=True, remove_reactions=True)
	paginator.add_reaction('⏮️', "first")
	paginator.add_reaction('⏪', "back")
	paginator.add_reaction('🔐', "lock")
	paginator.add_reaction('⏩', "next")
	paginator.add_reaction('⏭️', "last")
	#print(len(embeds))
	await paginator.run(embeds)
	return
'''
@bot.command(name='rst',
             aliases=[],
             help=': Creates a new message to have reaction roles on')
async def rst(ctx):
	for key in db.keys():
		del db[key]
	#db["leaderboard"] = {}
	for key, value in db.items():
		print(key, value)
'''




keep_alive.keep_alive()

bot.run(TOKEN)
