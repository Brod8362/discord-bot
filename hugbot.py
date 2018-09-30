#!/usr/bin/env python3
#import all the things, if in NP++ i recommend alt+1 
import discord #must be installed
import asyncio
from discord.ext import commands 
client = discord.Client()
import random
import sys
import logging
import traceback
import re 
import string
import requests #must be installed
from bs4 import BeautifulSoup #must be installed
import yaml #must be installed
import urllib.parse
import io 
from PIL import Image #must be installed
import math
import os.path
from distutils import util
import functools
import time
import unicodedata
import itertools

#some global variables
p = "[" # this is the prefix the bot will use to respond to commands
genericlist = []
#variables for storage

serverconfig = {}


#log stuff
logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.INFO)
logger = logging.getLogger("test-bot")

if not os.path.isfile("serverdata.yml"):
	open("serverdata.yml", "w+")

config = {}
#reading configs
with open("config.yaml", "r") as stream:
	config = (yaml.load(stream))
		

with open("serverdata.yml", "r") as stream:
	serverconfig = (yaml.load(stream))
	if serverconfig == None:
		serverconfig = {}
 
p = config["prefix"]
adminid = config["adminid"]

#for getting information from users
async def get_user(id):
	id = str(id)
	user = next((server.get_member(id) for server in client.servers), None)
	if user:
		return user
	user = await client.get_user_info(id)
	return user

#lets make me a good embed
def embed_gen(title=None, desc=None, color=0x4f545c, author=None, footer_content=None, footer_icon_url=None, image_url=None, type=None, footer_author=False, footer_author_id=False): #str, str, hex, discord.User(), str, str, str, str, bool, bool
		#Some words on the types: if you specify a type, your title and color are overriden. Types are eventually going to be moved to a separate file, where you can add your own custom types. 
	if type != None:
		if type == "error":
			title = "Error" 
			color = 0xFF0000
		elif type == "info":
			title = "\U00002139 Information"
			color = 0x007F00
		elif type == "warn":
			title = "\U000026A0 Warning"
			color = 0xFF0000
		elif type == "pass":
			title = "asd"
			color = 0x00FF00
	embed = discord.Embed(title=title, description=desc, color=color)
	if author != None and footer_author == False:
		embed.set_author(name=author.name,icon_url=author.avatar_url)
	if footer_author:
		if footer_author_id:
			embed.set_footer(text=f"{author.name} ({author.id})", icon_url=author.avatar_url)
		else:
			embed.set_footer(text=author.name, icon_url=author.avatar_url)
	else:
		if footer_content != None:
			embed.set_footer(text=footer_content, icon_url=footer_icon_url)
	if image_url != None:
		embed.set_image(url=image_url)

		
	return embed
	
def check_admin(member):
	return member.server_permissions.administrator


def check_bot_admin(member):
	if str(member.id) == str(adminid):
		return True
	return False

def get_content(session, search_class, site, attributes=None, limit=None, params=None): #requests.Session(), str, str, dict, int, dict
	page = session.get(site, params=params)
	soup = BeautifulSoup(page.content, "html.parser")
	results = soup.find_all(search_class, attrs=attributes, limit=limit) 
	found = len(results)
	if limit == 1:
		return results[0], found
	return results, found

def create_server_config(serverid): #str, needs server id NOT server object
	serverconfig[serverid] = {"keys":set(), "nsfw_channels":set(), "log_channel":None, "extra_options":{}}
	upgrade_server_config(serverid)

def save_server_config(): 
	with open('serverdata.yml', 'w') as outfile:
		yaml.dump(serverconfig, outfile, default_flow_style=False)


def upgrade_server_config(server): #this is only used for updating older configs, and as such WILL NOT have all variables, only ones added since the initial release. 
	if not "extra_options" in serverconfig[server]: #to do: CLEANUP THIS NIGHTMARE
		serverconfig[server]["extra_options"] = {}
	if not "nadeko_logging" in serverconfig[server]["extra_options"]:
		serverconfig[server]["extra_options"]["nadeko_logging"] = 0
	if not "user_stats" in serverconfig[server]:
		serverconfig[server]["user_stats"] = {}
	if not "messages" in serverconfig[server]["user_stats"]:
		serverconfig[server]["user_stats"]["messages"] = {}
	if not "images" in serverconfig[server]["user_stats"]:
		serverconfig[server]["user_stats"]["images"] = {}
	if not "reactions_rx" in serverconfig[server]["user_stats"]:
		serverconfig[server]["user_stats"]["reactions_rx"] = {}
	if not "reactions_tx" in serverconfig[server]["user_stats"]:
		serverconfig[server]["user_stats"]["reactions_tx"] = {}
	if not "watched_users" in serverconfig[server]:
		serverconfig[server]["watched_users"] = set()
	if not "voice_logging" in serverconfig[server]["extra_options"]:
		serverconfig[server]["extra_options"]["voice_logging"] = 1
	if not "watched_roles" in serverconfig[server]:
		serverconfig[server]["watched_roles"] = set()
	if not "excluded_channels" in serverconfig[server]:
		serverconfig[server]["excluded_channels"] = set()
	if not "deleted_messages" in serverconfig[server]["user_stats"]:
		serverconfig[server]["user_stats"]["deleted_messages"] = {}
	save_server_config()

	
	

async def check_for_keys(message): #used to check for watch keys in messages
	content = message.content #key watching
	if message.channel.id in serverconfig[message.server.id]["excluded_channels"]:
		return
	try:
		if serverconfig[message.server.id]["keys"]:
			keys_escaped = "|".join(serverconfig[message.server.id]["keys"])
			content = re.sub(f"((?:{keys_escaped})+)", r"**\1**", content, flags=re.IGNORECASE)
		if content != message.content:
			embed = embed_gen(title=f"Keyword Detected in {message.channel.name}", author=message.author, footer_author=True, footer_author_id=True, desc=content)
			await client.send_message(client.get_channel(serverconfig[message.server.id]["log_channel"]), embed=embed)
	except:
			await client.send_message(client.get_channel(serverconfig[message.server.id]["log_channel"]), f"big ouchie! \n ```{traceback.format_exc()}```")
			traceback.print_exc()


def add_to_msg_count(message):
	userid = message.author.id
	serverid = message.server.id
	try:
		serverconfig[serverid]["user_stats"]["messages"][userid] += 1
	except KeyError:
		serverconfig[serverid]["user_stats"]["messages"][userid] = 1
		serverconfig[serverid]["user_stats"]["images"][userid] = 0
		serverconfig[serverid]["user_stats"]["reactions_rx"][userid] = 0
		serverconfig[serverid]["user_stats"]["reactions_tx"][userid] = 0
		serverconfig[serverid]["user_stats"]["deleted_messages"][userid] = 0
	if message.attachments:
		try:
			serverconfig[serverid]["user_stats"]["images"][userid] += 1
		except KeyError:
			serverconfig[serverid]["user_stats"]["images"][userid] = 1
	if not userid in serverconfig[serverid]["user_stats"]["deleted_messages"]:
			serverconfig[serverid]["user_stats"]["deleted_messages"][usr.id] = 0
		

def add_to_del_count(message):
	userid = message.author.id
	serverid = message.server.id
	try:
		serverconfig[serverid]["user_stats"]["deleted_messages"][userid] += 1
	except KeyError:
		serverconfig[serverid]["user_stats"]["deleted_messages"][userid] = 1

		
def add_to_reaction_count(user, message, rx=False): #rx as in recieve, think radio transmission, and yes i know it's a terrible name but i literally do not care
	serverid = message.server.id
	userid = user.id
	if rx:
		try:
			serverconfig[serverid]["user_stats"]["reactions_rx"][userid] += 1
		except KeyError:
			serverconfig[serverid]["user_stats"]["reactions_rx"][userid] = 1
	else:
		try:
			serverconfig[serverid]["user_stats"]["reactions_tx"][userid] += 1
		except KeyError:
			serverconfig[serverid]["user_stats"]["reactions_tx"][userid] = 1

async def check_for_role_pings(message, deleted=False):
	delstring = ""
	if deleted == True:
		delstring = "Deleted "
	if message.role_mentions:
		for role in message.role_mentions:
			if role.id in serverconfig[message.server.id]["watched_roles"]:
				embed = embed_gen(title=f"{delstring}Role ping in #{message.channel.name}", author=message.author, footer_author=True, footer_author_id=True, desc=message.content)
				await client.send_message(client.get_channel(serverconfig[message.server.id]["log_channel"]), embed=embed)

async def reactify(message, question, choices=None, show_return=False, boolean=False, toggles=False): #choices is a dict of things, where the key is what the bot shows and the value is what it returns when the option is picked
	numdict = {}
	string = ""
	def num_to_emoji(n):
		if n < 0 or n > 9:
			raise Exception("OutOfRange")
		return str(n) + "\N{Combining Enclosing Keycap}"
	def emoji_to_num(e):
		return e[0]
	i = 1
	if boolean: #true/false options
		ask = await client.send_message(message.channel, embed=embed_gen(desc=question))
		await client.add_reaction(ask, "\N{WHITE HEAVY CHECK MARK}")
		await client.add_reaction(ask, "\N{NO ENTRY SIGN}")
		while True:
			reply = await client.wait_for_reaction(message=ask, user=message.author, timeout=30)
			if not reply:
				await client.add_reaction(ask, "\N{CLOCK FACE TEN-THIRTY}")
				break
			if reply.reaction.emoji == "\N{WHITE HEAVY CHECK MARK}":
				return True, ask
			elif reply.reaction.emoji == "\N{NO ENTRY SIGN}":
				return False, ask

	for x in choices: #for dicts
		numdict[i] = x
		try:
			emoji = num_to_emoji(i) 
		except Exception as OutOfRange:
			emoji = "\N{NO ENTRY SIGN}"
		if show_return:
			try: 
				string += f"{emoji}{x} ({choices[x]})\n"
			except Exception as OutOfRange:
				string += f"\N{NO ENTRY SIGN} {x}\n"
		if not show_return:
			toggle_state=""
			if toggles: #for the "toggles" mode
				if not choices[x]:
					toggle_state = "\N{NO ENTRY SIGN}"
				else:
					toggle_state = "\N{WHITE HEAVY CHECK MARK}"
			string += f"{emoji}{toggle_state} {x}\n"
		i += 1
	embed = embed_gen(title=question, desc=string)	
	ask = await client.send_message(message.channel, embed=embed)
	i = 1
	while i <= len(choices):
		try:
			await client.add_reaction(ask, num_to_emoji(i))	
		except Exception as OutOfRange:
			await client.add_reaction(ask, "\N{NO ENTRY SIGN}")
			break
		await asyncio.sleep(0.5)
		i += 1
	reply = await client.wait_for_reaction(message=ask, user=message.author, timeout=30)
	choice = int(emoji_to_num(reply.reaction.emoji))
	final = choices[numdict[choice]] #for regular operation
	alt_final = numdict[choice] #for the toggles option
	if toggles:
		await client.edit_message(ask, embed=embed_gen(desc=f"Do what with `{alt_final}`?"))
		await client.add_reaction(ask, "\N{WHITE HEAVY CHECK MARK}")
		await client.add_reaction(ask, "\N{NO ENTRY SIGN}")
		reply = await client.wait_for_reaction(message=ask, user=message.author, timeout=30)
		if not reply:
			await client.add_reaction(ask, "\N{CLOCK FACE TEN-THIRTY}")
			#figure out what to do here
		if reply.reaction.emoji == "\N{WHITE HEAVY CHECK MARK}":
			return alt_final, ask, True
		elif reply.reaction.emoji == "\N{NO ENTRY SIGN}":
			return alt_final, ask, False
	return final, ask

	

def log_message(message):
	logger.info(f"({message.server.name}) ({message.channel.name}) | {message.author.name}: {message.content}")


#only works if the first argument of the function it wraps is the message
def handle_exceptions(f):
	@functools.wraps(f)
	async def inner(message, *args, **kwargs):
		try:
			return await f(message, *args, **kwargs)
		except:
			await client.send_message(message.channel, f"big ouchie!\n```\n{traceback.format_exc()}\n```")
	return inner


class CommandRegistry:
	def __init__(self, prefix):
		self.commands = {}
		self.help = {}
		self.syntax = {}
		self.admin = {}
		self.sadmin = {}
		self.prefix = prefix
		
	def __iter__(self):
		return iter(self.commands.keys())
	
	def register(self, name, help="No Help defined.", syntax="", admin=False, bot_admin=False):
		def wrap(f):
			self.commands[name] = f
			self.help[name] = help
			self.syntax[name] = syntax
			self.admin[name] = admin
			self.sadmin[name] = bot_admin
			return f
		return wrap
		

	def get(self, name):
		if not name.startswith(self.prefix):
			return None
		return self.commands.get(name[len(self.prefix):])
	
	def get_help(self, name, user):
		admin = check_admin(user)
		
		if  not self.admin[name] and not self.sadmin[name]: #regular commands
			return self.help[name]
		elif admin and self.admin[name]: #for admin commands
			return self.help[name]+" **[ADMIN]**"
		elif check_bot_admin(user) and self.sadmin[name]: #superadmin commands
			return self.help[name]+" **[BOT ADMIN]**"
		else:
			return None
	
	def get_syntax(self, name):
		return self.syntax[name]

	def get_permission(self, name):
		if self.admin[name] == True:
			return "admin"
		elif self.sadmin[name] == True:
			return "sadmin"
		else:
			return "regular"

commands = CommandRegistry(p) #this is the prefix 
###START CLIENT EVENTS

@client.event
async def on_reaction_add(reaction, user):
	add_to_reaction_count(user, reaction.message)
	add_to_reaction_count(reaction.message.author, reaction.message, rx=True)


@client.event
async def on_message_delete(message):
	await check_for_role_pings(message, deleted=True)
	add_to_del_count(message)

@client.event
async def on_voice_state_update(before, after):
	if before.id in serverconfig[before.server.id]["watched_users"] and serverconfig[before.server.id]["extra_options"]["voice_logging"]: 
		timex = time.strftime("%H:%M:%S")
		if not before.voice.voice_channel: #joining
			embed = embed_gen(title=f"Voice State Change {timex} GMT", author=before, footer_author=True, footer_author_id=True, desc=f"\N{SPEAKER}\N{INBOX TRAY}{before.mention} joined `{after.voice.voice_channel.name}`", color=0xff66ff)
			await client.send_message(client.get_channel(serverconfig[before.server.id]["log_channel"]), embed=embed)
		if before.voice.voice_channel and after.voice.voice_channel: #changing channels (like on TV but much more exciting)
			if before.voice.voice_channel.id == after.voice.voice_channel.id: #this is to catch things like muting and deafening
				return
			embed = embed_gen(title=f"Voice State Change {timex} GMT", author=before, footer_author=True, footer_author_id=True, desc=f"\N{SPEAKER}\N{TWISTED RIGHTWARDS ARROWS}{before.mention} moved from `{before.voice.voice_channel.name}` to `{after.voice.voice_channel.name}`", color=0xff66ff)
			await client.send_message(client.get_channel(serverconfig[before.server.id]["log_channel"]), embed=embed)
		
		elif before.voice.voice_channel: #leaving
			embed = embed_gen(title=f"Voice State Change {timex} GMT", author=before, footer_author=True, footer_author_id=True, desc=f"\N{SPEAKER}\N{OUTBOX TRAY}{before.mention} left `{before.voice.voice_channel.name}`", color=0xff66ff)
			await client.send_message(client.get_channel(serverconfig[before.server.id]["log_channel"]), embed=embed)



@client.event
async def on_message_edit(before, after):
	await check_for_keys(after)
	await check_for_role_pings(after)


@client.event
async def on_message(message):
	if config["log_all_messages"]:
		log_message(message)
	if message.author.bot:
		return
	if not message.server.id in serverconfig:
		create_server_config(message.server.id)
	add_to_msg_count(message)
	await check_for_role_pings(message)
	if serverconfig[message.server.id]["extra_options"]["nadeko_logging"] == 1:
		if message.content.startswith(".. "):
			cmd, key, content = message.content.split(" ", 2)
			embd = embed_gen(title="Quote Created", desc=f"**{message.author.mention}** created quote **{key}** with content **{content}**", color=0x000000, author=message.author, footer_author=True, footer_author_id=True)
			channelset = message.server.get_channel(serverconfig[message.server.id]["log_channel"])
			await client.send_message(channelset, embed=embd)
		elif message.content.startswith(".qdel "): #nadeko logging 
			confirmation = await client.wait_for_message(author=await get_user("116275390695079945")) #this is the nadeko bot user
			if "deleted." in confirmation.embeds[0]["description"]:
				cmd, id, = message.content.split(" ", 1)
				embd = embed_gen(title="Quote Deleted", desc=f"**{message.author.mention}** deleted quote **{id}**", color=0xFF0000, author=message.author, footer_author=True, footer_author_id=True)
				channelset = message.server.get_channel(serverconfig[message.server.id]["log_channel"])
				await client.send_message(channelset, embed=embd)
	

	await check_for_keys(message) #key watching
	
	try:
		cmd = commands.get(message.content.split()[0])
	except IndexError:
		return
	cmdname = message.content.split()[0].replace(p, "")
	if cmd:
		if commands.get_permission(cmdname) == "regular": #for regular commands
			await cmd(message)
			return
		elif commands.get_permission(cmdname) == "admin" and check_admin(message.author): #for admin commands
			await cmd(message)
			return
		elif commands.get_permission(cmdname) == "sadmin" and check_bot_admin(message.author): #for bot admin commands
			await cmd(message)
			return
		else:
			await client.add_reaction(message, "🚫")
		
### END CLIENT EVENTS


### START COMMANDS
@commands.register("help", help="Shows help for all available commands, or a specific command if specified.", syntax=f"(command or NONE)")
async def cmd_help(message):
	command = f"{p}help"
	try:
		command, msg = message.content.split(' ', 1)
	except ValueError:
		string = ""
		for cmd in commands:
			hlp = commands.get_help(cmd, message.author)
			if hlp != None:
				string = string+f"\n**{cmd}**: {hlp}"
		embd = embed_gen(title="List of Commands", desc=string, author=message.author)
		await client.send_message(message.channel, embed=embd)
		return
	else:
		try:
				helpinfo = commands.get_help(msg, message.author)
		except KeyError:
			embd = embed_gen(title="\U0000274C Error", desc="Command not found.", color=0xFF0000, author=message.author)
			await client.send_message(message.channel, embed=embd)
			return
		syninfo = commands.get_syntax(msg)
		embd = embed_gen(title=f"Help for: {msg}", desc=f"{helpinfo}\n**Syntax:**```{p}{msg} {syninfo}```", author=message.author, footer_author=True)
		await client.send_message(message.channel, embed=embd)

@commands.register("stop", help=f"Stops the bot.", syntax=f"(f)'", bot_admin = True)
async def cmd_stop(message):

		output, ask = await reactify(message, "Do you want to shut down the bot?", boolean=True)
		if output:
			save_server_config()
			await client.add_reaction(ask, "\N{REGIONAL INDICATOR SYMBOL LETTER K}")
			await client.close()
			sys.exit()

@commands.register("invite", help="Creates an invite link for the bot.", syntax=f"", bot_admin=True)
async def cmd_invite(message):
	await client.send_message(message.channel, f"https://discordapp.com/oauth2/authorize?&client_id={client.user.id}&scope=bot&permissions=0")

@commands.register("configure", admin=True)
async def cmd_configure(message):
	dict = {}
	for x in serverconfig[message.server.id]["extra_options"]:
		print(x)
		dict[x] = serverconfig[message.server.id]["extra_options"][x]
	option, ask, change = await reactify(message, "Choose an option:", choices=dict, toggles=True)	
	serverconfig[message.server.id]["extra_options"][option] = change
	await client.edit_message(ask, embed=embed_gen(desc=f"`{option}` changed to {change}."))
	save_server_config()
@commands.register("sankaku", help="Retrieves image(s) from Sankaku using specified tags.", syntax=f"(tags)")
async def cmd_sankaku(message):
	if message.channel.id not in serverconfig[message.server.id]["nsfw_channels"]:
		await client.send_message(message.channel, "NSFW is not enabled in this channel.")
		return
	await client.send_typing(message.channel)
	session = requests.Session()
	session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',})
	tagsraw = message.content.split(' ')
	tagsraw.remove(tagsraw[0])
	tags = " ".join(tagsraw)
	results, number_found = get_content(session, 'span', "https://chan.sankakucomplex.com", attributes={"class":"thumb"}, params={"tags":tags, "commit":"Search"})
	if number_found == 0:
		await client.send_message(message.channel, f"No results found for `{tags.replace(' ',', ')}`.")
		return
	chosen = random.randint(1, number_found)
	pick = results[chosen-1].attrs['id'].replace("p","")	
	image, number_found = get_content(session, 'img', f"https://chan.sankakucomplex.com/post/show/{pick}", attributes={"id":"image"}, limit=1)
	image_local = session.get(f"http:{image.attrs['src']}")
	image_name, trash = image_local.url.split("/")[-1].split("?")
	await client.send_file(message.channel, filename=image_name, fp=io.BytesIO(image_local.content), content=f"```Tags used: {tags.replace('+',', ')} \n https://chan.sankakucomplex.com/post/show/{pick}```")
	#await client.send_message(message.channel, f'Tags used: **{tags.replace("+",", ")}** \n http://{image.attrs["src"].replace("//","")}')

@commands.register("gelbooru", help="Retrieves image(s) from gelbooru using specified tags.", syntax=f"(tags)")
async def cmd_gelbooru(message):
	if message.channel.id not in serverconfig[message.server.id]["nsfw_channels"]:
		await client.send_message(message.channel, "NSFW is not enabled in this channel.")
		return
	await client.send_typing(message.channel)
	session = requests.Session()
	session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',})
	tagsraw = message.content.split(' ')
	tagsraw.remove(tagsraw[0])	
	tags = " ".join(tagsraw)
	results, number_found = get_content(session, 'span', "https://gelbooru.com/index.php?", attributes={"class":"thumb"}, params={"tags":tags, "page":"post","s":"list"})
	if number_found == 0:
		await client.send_message(message.channel, f"No results found for {tags.replace(' ',', ')}.")
		return
	chosen = random.randint(1, number_found)
	pick = results[chosen-1].attrs['id'].replace("s","")
	image, number_found = get_content(session, 'img', f"https://gelbooru.com/index.php?", attributes={"id":"image"}, params={"page":"post", "s":"view", "id":pick}, limit=1)
	await client.send_message(message.channel, f'```Tags used: {tags.replace("+",", ")} \n https://gelbooru.com/index.php?page=post&s=view&id={pick}``` \n {image.attrs["src"]}')
	
	
	
	
@commands.register("nsfw", help="Enable or Disable NSFW in a channel.",admin=True)
async def cmd_nsfw(message):
	status = ""
	if message.channel.id in serverconfig[message.server.id]["nsfw_channels"]:
		status = "On"
	else:
		status = "Off"
	choice = await client.send_message(message.channel, f"NSFW Status for channel **{message.channel.mention}** is **{status}**. React with \u274C to disable it and \u2705 to enable it.")
	await client.add_reaction(choice, "\u274C")
	await client.add_reaction(choice, "\u2705")
	output = await client.wait_for_reaction(message=choice, user=message.author, timeout=30, emoji=["\u274C","\u2705"])
	emoji = output[0].emoji
	if emoji == "\u2705":
		await client.edit_message(choice, new_content=f"NSFW **Enabled** in **{message.channel.mention}**")
		if not message.channel.id in serverconfig[message.server.id]["nsfw_channels"]:
			serverconfig[message.server.id]["nsfw_channels"].add(message.channel.id)
	elif emoji == "\u274C":
		await client.edit_message(choice, new_content=f"NSFW **Disabled** in **{message.channel.mention}**")
		if message.channel.id in serverconfig[message.server.id]["nsfw_channels"]:
			serverconfig[message.server.id]["nsfw_channels"].add(message.channel.id)
	save_server_config()


@commands.register("uinfo", help="Find various information about a user.", syntax="(userid or NONE)")
async def cmd_uinfo(message):
	try:
		command, msg = message.content.split(" ", 1)
	except ValueError:
		usr = message.author
	else:
		try:
			usr = await find(message, term=msg)
		except:
			pass
	if usr is None:
		await client.send_message(message.channel, "No user found.")
		return
	embed = embed_gen(title=f"{usr.name}#{usr.discriminator}")
	embed.set_thumbnail(url=usr.avatar_url)
	if not usr.id in serverconfig[message.server.id]["user_stats"]["messages"]:
		values = ['messages', 'images', 'reactions_tx', 'reactions_rx', 'deleted_messages'] 
		for value in values:
			serverconfig[message.server.id]["user_stats"][value][usr.id] = 0

	fields = { #add fields to display here, they're done in order as shown here
	"Nickname":usr.display_name,
	"ID":usr.id,
	"Joined At":usr.joined_at,
	"Account Creation Date":usr.created_at,
	"Messages Sent":serverconfig[message.server.id]["user_stats"]["messages"][usr.id],
	"Images/Attachments Sent":serverconfig[message.server.id]["user_stats"]["images"][usr.id],
	"Reactions Recieved":serverconfig[message.server.id]["user_stats"]["reactions_rx"][usr.id],
	"Reactions Given":serverconfig[message.server.id]["user_stats"]["reactions_tx"][usr.id],
	"Messages Deleted":serverconfig[message.server.id]["user_stats"]["deleted_messages"][usr.id]
	}
	for entry in fields:
		embed.add_field(name=entry, value=fields[entry])
	await client.send_message(message.channel, embed=embed)
		
@commands.register("sinfo", help="Find information about the server the command is run in.")
async def cmd_sinfo(message):
	server = message.server
	embd = embed_gen(desc=f"**Name:** {server.name}\n**Region:** {server.region}\n**Member Count:** {server.member_count}\n**Owner:** {server.owner.name}#{server.owner.discriminator}", type="info")
	await client.send_message(message.channel, embed=embd)	

@commands.register("servers", help="See all servers the bot is in.", bot_admin=True)
async def cmd_servers(message):
	string = ""
	for server in client.servers:
		string += f"{server.name} \n"
	embd = embed_gen(title=f"Servers [{len(client.servers)}]", desc=string)
#footer_content=f"{str(len(client.servers))} servers",footer_icon_url=None)
	await client.send_message(message.channel, embed=embd)
	try:
		command, msg = message.content.split(" ", 1)
	except ValueError:
		usr = message.author
	else:
		try:
			usr = await find(message, term=msg)
		except:
			pass
	if usr is None:
		await client.send_message(message.channel, "No user found.")
		return


@commands.register("logchannel", help="Sets the current channel as the log channel.", admin=True)
async def cmd_logchannel(message):
	if not message.server.id in serverconfig:
		create_server_config(message.server.id)
	serverconfig[message.server.id]["log_channel"] = message.channel.id
	await client.send_message(message.channel, f"Log channel has been set to {message.channel.mention}")
	save_server_config()

@commands.register("8ball", help="Ask the all-seeing 8 ball a question.")
async def cmd_8ball(message):
	random_choices = ["It is certain.", "It is decidedly so.", "Without a doubt.", "Yes - definitely.", "You may rely on it.", "As I see it, yes.", "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.", "Reply hazy, try again", "Ask again later.", "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.", "Don't count on it.", "My reply is no.", "My sources say no", "Outlook not so good.", "Very doubtful."]
	choice = random.choice(random_choices)
	await client.send_message(message.channel, choice)

@commands.register("keys", help="Manage server keywords.", syntax="(add|del|list|clear|help) (key or NONE)", admin=True)
async def cmd_keys(message):
	try:
		cmd, option, args = message.content.split(" ", 2)	
	except:
		try:
			cmd, option = message.content.split(" ", 1)
		except:
			option = None
	if option == "add":
		try:
			if serverconfig[message.server.id] == None:
				pass
		except KeyError:
			create_server_config(message.server.id)
		try:
			re.compile(args)
		except:
			await client.send_message(message.channel, "Invalid Regular Expression.")
			return	
		serverconfig[message.server.id]["keys"].add(args)
		await client.send_message(message.channel, f"Added {args} to server keywords.")
		save_server_config()
	elif option == "remove" or option == "del":
		try:
			serverconfig[message.server.id]["keys"].remove(args)
		except:
			await client.send_message(message.channel, "That key isn't in the server keywords")
			return
		await client.send_message(message.channel, f"{args} has been removed from server keywords.")	
		save_server_config()
	elif option == "list":
		formatted_keys = map(lambda x: f"`{x}`" , serverconfig[message.server.id]["keys"])
		string = ", ".join(formatted_keys)
		if not string:
			string = "There are no watch keys."
		await client.send_message(message.channel, string)
	elif option == "clear":
		serverconfig[message.server.id]["keys"] = set()
		await client.send_message(message.channel, "All server keys cleared.")
		save_server_config()
	elif option == None or option == "help":
		await client.send_message(message.channel, "Available options: `add`, `del`, `list`, `clear`, `help`") 
	
@commands.register("dbupdate", help="Update the server's data file. Useful if you're having issues with newer commands.", admin=True)
async def cmd_dbupdate(message):
	upgrade_server_config(message.server.id)
	await client.send_message(message.channel, "The data file for this server has been updated.")

@commands.register("github", help="Provides a link to the github repo for the bot source code.")
async def cmd_github(message):
	await client.send_message(message.channel, "Here's a link to the Github repository for this bot: https://github.com/Brod8362/discord-bot")

async def find(message, term=None):	
	user = None
	if term:
		term = term.lower()
	if message.mentions != []: #mentions
		user = message.mentions[0]
	else:
		for member in message.server.members: #for every member in the server,
			if term in member.name.lower(): #check username
				user = member
				break
			elif term == member.id: #check snowflake ID
				user = member
				break
			elif member.nick: #check nickname
				if term in  member.nick.lower():
					user = member
					break
	if not user:
		return None
	return user

@commands.register("watch", help="Manage watched users.", syntax="(add|del|list|clear|help) (key or NONE)", admin=True)
async def cmd_watch(message):
	try:
		cmd, option, args = message.content.split(" ", 2)	
	except:
		try:
			cmd, option = message.content.split(" ", 1)
		except:
			option = None
	if option == "add":
		try:
			if serverconfig[message.server.id] == None:
				pass
		except KeyError:
			create_server_config(message.server.id)
		member = await find(message, args)
		if not member:
			await client.send_message(message.channel, "User not found.")
			return
		serverconfig[message.server.id]["watched_users"].add(member.id)
		await client.send_message(message.channel, f"Added {member.id} to watched users.")
		save_server_config()
	elif option == "remove" or option == "del":
		try:
			serverconfig[message.server.id]["watched_users"].remove(args)
		except:
			await client.send_message(message.channel, "That ID isn't in the watched users.")
			return
		await client.send_message(message.channel, f"{args} has been removed from the watched users.")	
		save_server_config()
	elif option == "list":
		formatted_keys = map(lambda x: f"<@{x}>" , serverconfig[message.server.id]["watched_users"])
		string = ", ".join(formatted_keys)
		if not string:
			string = "There are no watched users."
		await client.send_message(message.channel, string)
	elif option == "clear":
		serverconfig[message.server.id]["keys"] = set()
		await client.send_message(message.channel, "All watched users removed.")
		save_server_config()
	elif option == "help":
		await client.send_message(message.channel, "Available options: `add`, `del`, `list`, `clear`, `help`") 
	else:
		member = await find(message, option)
		if not member:
			await client.send_message(message.channel, "Available options: `add`, `del`, `list`, `clear`, `help`")
		else:
			serverconfig[message.server.id]["watched_users"].add(member.id)
			await client.send_message(message.channel, f"Added {member.id} to watched users.") 

@commands.register("rw", help="Manage watched roles.", admin=True,syntax="(add|del|list|clear|help)")
async def cmd_rw(message):
	try:
		cmd, option = message.content.split(" ", 1)
	except:
		option = None
	if option == "add":
		roledict = {}
		for role in message.server.roles:
			if role.mentionable and not role.id in serverconfig[message.server.id]["watched_roles"]:
				roledict[f"<@&{role.id}>"] = role.id
		roleid, ask = await reactify(message, "Which role do you want to add?", choices=roledict, show_return=True)
		serverconfig[message.server.id]["watched_roles"].add(roleid)
		await client.edit_message(ask, embed=embed_gen(desc=f"Added <@&{roleid}> to the role watch list."))
		save_server_config()
	elif option == "remove" or option == "del":
		roledict = {}
		for x in serverconfig[message.server.id]["watched_roles"]:
			roledict[f"<@&{x}>"] = x
		roleid, ask = await reactify(message, "Which role do you want to remove?", choices=roledict, show_return=True)
		serverconfig[message.server.id]["watched_roles"].remove(roleid)
		await client.edit_message(ask, embed=embed_gen(desc=f"Removed <@&{roleid}> from the role watch list."))	
		save_server_config()
	elif option == "list":
		formatted_keys = map(lambda x: f"<@&{x}> ({x})" , serverconfig[message.server.id]["watched_roles"])
		string = "\n".join(formatted_keys)
		if not string:
			string = "There are no watched roles."
		embed = embed_gen(title="Watched Roles", desc=string)
		await client.send_message(message.channel, embed=embed)
	elif option == "clear":
		serverconfig[message.server.id]["watched_roles"] = set()
		await client.send_message(message.channel, "All watched roles removed.")
		save_server_config()
	elif option == "help" or option == None:
		await client.send_message(message.channel, "Available options: `add`, `del`, `list`, `clear`, `help`") 


@commands.register("exclude", help="Manage excluded channels.", syntax="(add|del|list|clear|help) (key or NONE)", admin=True)
async def cmd_watch(message):
	try:
		cmd, option, args = message.content.split(" ", 2)	
	except:
		try:
			cmd, option = message.content.split(" ", 1)
		except:
			option = None
	if option == "add":
		try:
			if serverconfig[message.server.id] == None:
				pass
		except KeyError:
			create_server_config(message.server.id)
		serverconfig[message.server.id]["excluded_channels"].add(args)
		await client.send_message(message.channel, f"Added {args} to watched users.")
		save_server_config()
	elif option == "remove" or option == "del":
		try:
			serverconfig[message.server.id]["excluded_channels"].remove(args)
		except:
			await client.send_message(message.channel, "That ID isn't in the excluded channels.")
			return
		await client.send_message(message.channel, f"{args} has been removed from the excluded channels.")	
		save_server_config()
	elif option == "list":
		formatted_keys = map(lambda x: f"<#{x}>" , serverconfig[message.server.id]["excluded_channels"])
		string = ", ".join(formatted_keys)
		if not string:
			string = "There are no excluded channels."
		await client.send_message(message.channel, string)
	elif option == "clear":
		serverconfig[message.server.id]["excluded_channels"] = set()
		await client.send_message(message.channel, "All excluded channels removed.")
		save_server_config()
	elif option == "help":
		await client.send_message(message.channel, "Available options: `add`, `del`, `list`, `clear`, `help`, `here`") 
	elif option == "here":
		if not message.channel.id in serverconfig[message.server.id]["excluded_channels"]:
			serverconfig[message.server.id]["excluded_channels"].add(message.channel.id)
			await client.send_message(message.channel, "Added current channel to exclude list.")
		else:
			serverconfig[message.server.id]["excluded_channels"].remove(message.channel.id)
			await client.send_message(message.channel, "Removed current channel from exclude list.")
	else:
		await client.send_message(message.channel, "Available options: `add`, `del`, `list`, `clear`, `help`, `here`")


async def start_auto_save():
	while True:
		await asyncio.sleep(300)
		logger.info("Server configs saved")
		save_server_config()
		

#this always needs to be at the end, dont forget retard		
@client.event
async def on_ready():
	await client.change_presence(game=discord.Game(name=f'{p}help for help'))
	logger.info("Logged in as:")
	logger.info(client.user.name)
	logger.info(client.user.id)	
	logger.info(' ')
	logger.info("Owner Information:")
	AppInfo = await client.application_info()
	logger.info(AppInfo.owner.name)
	logger.info(AppInfo.owner.id)
	if config["adminid"] == "auto":
		logger.info("Admin ID set to auto, defaulting to bot owner.")
		global adminid
		adminid = AppInfo.owner.id
	for x in serverconfig:
		upgrade_server_config(x)
	logger.info("All server configs are up to date.")
	await start_auto_save()




client.run(config["token"])


