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


#some global variables
currentvoice = {}	#this is used in voice commands
npinfo = {} # this is for ]nowplaying
playqueue_by_server = {} #this is for queueing shit 
p = "[" # this is the prefix the bot will use to respond to commands
genericlist = []
#voiceid = str(message.author.id+str(message.server.id))
#blacklistdir = "C:/Users/Blake/Documents/Actual Documents/Discord Bot/blacklist.txt" #directory for blacklist file, if not present blacklist is ersaed on reboot
#blacklist = set(line.strip() for line in open(blacklistdir)) #loads blcaklist into set blacklist.
#variables for storage n shit

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
async def embed_gen(title=None, desc=None, color=0x000000, author=None, footer_content=None, footer_icon_url=None, image_url=None, type=None, footer_author=False, footer_author_id=False): #str, str, hex, discord.User(), str, str, str, str, bool, bool
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
		embed.set_image(image_url)

		
	return embed
	
async def check_admin(member):
	return member.server_permissions.administrator

async def check_bot_admin(member):
	if str(member.id) == str(adminid):
		return True
	return False

async def get_random(max):
	return random.randint(1,max)
	
async def get_content(session, search_class, site, attributes=None, limit=None, params=None): #requests.Session(), str, str, dict, int, dict
	page = session.get(site, params=params)
	soup = BeautifulSoup(page.content, "html.parser")
	results = soup.find_all(search_class, attrs=attributes, limit=limit) 
	found = len(results)
	if limit == 1:
		return results[0], found
	return results, found

async def create_server_config(serverid): #str, needs server id NOT server object
	serverconfig[serverid] = {"keys":set(), "nsfw_channels":set(), "log_channel":None, "extra_options":{}}

def save_server_config(): 
	with open('serverdata.yml', 'w') as outfile:
		yaml.dump(serverconfig, outfile, default_flow_style=False)


async def upgrade_server_config(server): #this is only used for updating older configs, and as such WILL NOT have all variables, only ones added since the initial release. 
	if not "extra_options" in serverconfig[server]:
		serverconfig[server]["extra_options"] = {}
	if not "nadeko_logging" in serverconfig[server]["extra_options"]:
		serverconfig[server]["extra_options"]["nadeko_logging"] = 0
	if not "user_stats" in serverconfig[server]:
		serverconfig[server]["user_stats"] = {}
	save_server_config()
	
	

async def check_for_keys(message): #used to check for watch keys in messages
	content = message.content #key watching
	try:
		if serverconfig[message.server.id]["keys"]:
			keys_escaped = "|".join(serverconfig[message.server.id]["keys"])
			content = re.sub(f"((?:{keys_escaped})+)", r"**\1**", content, flags=re.IGNORECASE)
		if content != message.content:
			embed = await embed_gen(title=f"Keyword Detected in {message.channel.name}", author=message.author, footer_author=True, footer_author_id=True, desc=content)
			await client.send_message(client.get_channel(serverconfig[message.server.id]["log_channel"]), embed=embed)
	except:
			await client.send_message(client.get_channel(serverconfig[message.server.id]["log_channel"]), f"big ouchie! \n ```{traceback.format_exc()}```")
			traceback.print_exc()


async def add_to_msg_count(serverid, userid):
	try:
		serverconfig[serverid]["user_stats"][userid] += 1
	except KeyError:
		serverconfig[serverid]["user_stats"][userid] = 1
		


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
	
	async def get_help(self, name, user):
		admin = await check_admin(user)
		
		if  not self.admin[name] and not self.sadmin[name]: #regular commands
			return self.help[name]
		elif admin and self.admin[name]: #for admin commands
			return self.help[name]+" **[ADMIN]**"
		elif await check_bot_admin(user) and self.sadmin[name]: #superadmin commands
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





@client.event
async def on_message_edit(before, after):
	await check_for_keys(after)


@client.event
async def on_message(message):
	if message.author.bot:
		return
	await add_to_msg_count(message.server.id, message.author.id)

	if not message.server.id in serverconfig:
		await create_server_config(message.server.id)
	if serverconfig[message.server.id]["extra_options"]["nadeko_logging"] == 1:
		if message.content.startswith(".. "):
			cmd, key, content = message.content.split(" ", 2)
			embd = await embed_gen(title="Quote Created", desc=f"**{message.author.mention}** created quote **{key}** with content **{content}**", color=0x000000, author=message.author, footer_author=True, footer_author_id=True)
			channelset = message.server.get_channel(serverconfig[message.server.id]["log_channel"])
			await client.send_message(channelset, embed=embd)
		elif message.content.startswith(".qdel "): #nadeko logging 
			confirmation = await client.wait_for_message(author=await get_user("116275390695079945"))
			if "deleted." in confirmation.embeds[0]["description"]:
				cmd, id, = message.content.split(" ", 1)
				embd = await embed_gen(title="Quote Deleted", desc=f"**{message.author.mention}** deleted quote **{id}**", color=0xFF0000, author=message.author, footer_author=True, footer_author_id=True)
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
		elif commands.get_permission(cmdname) == "admin" and await check_admin(message.author): #for admin commands
			await cmd(message)
			return
		elif commands.get_permission(cmdname) == "sadmin" and await check_bot_admin(message.author): #for bot admin commands
			await cmd(message)
			return
		else:
			await client.add_reaction(message, "🚫")
		

@commands.register("help", help="Shows help for all available commands, or a specific command if specified.", syntax=f"(command or NONE)")
async def cmd_help(message):
	command = f"{p}help"
	try:
		command, msg = message.content.split(' ', 1)
	except ValueError:
		string = ""
		for cmd in commands:
			hlp = await commands.get_help(cmd, message.author)
			if hlp != None:
				string = string+f"\n**{cmd}**: {hlp}"
		embd = await embed_gen(title="List of Commands", desc=string, color=0x000000, author=message.author)
		await client.send_message(message.channel, embed=embd)
		return
	else:
		try:
				helpinfo = await commands.get_help(msg, message.author)
		except KeyError:
			embd = await embed_gen(title="\U0000274C Error", desc="Command not found.", color=0xFF0000, author=message.author)
			await client.send_message(message.channel, embed=embd)
			return
		syninfo = commands.get_syntax(msg)
		embd = await embed_gen(title=f"Help for: {msg}", desc=f"{helpinfo}\n**Syntax:**```{p}{msg} {syninfo}```", color=0x000000, author=message.author, footer_author=True)
		await client.send_message(message.channel, embed=embd)

@commands.register("stop", help=f"Stops the bot.", syntax=f"(f)'", bot_admin = True)
async def cmd_stop(message):
	command = f"{p}stop"
	try:
		command, arg = message.content.split(' ', 1)
	except ValueError:
		embd = await embed_gen(desc="Are you sure you want to shut down the bot? [Y/N]",type="warn")
		await client.send_message(message.channel, embed=embd)
		brod = message.author
		input = await client.wait_for_message(timeout=10.0, author=brod)
		if input.content.lower() == "y":
			#await client.send_message(message.channel,"**Shutting down.**")
			embd = await embed_gen(desc="Shutting down.", type="info")
			await client.send_message(message.channel, embed = embd)
			await client.close()
			sys.exit()
		else:
			embd = await embed_gen(desc="Shutdown cancelled", type="info")
			await client.send_message(message.channel, embed=embd)
	if arg == "f":
		await client.add_reaction(message, "\N{REGIONAL INDICATOR SYMBOL LETTER K}")
		await client.close()
		sys.exit()
		return

@commands.register("invite", help="Creates an invite link for the bot.", syntax=f"", bot_admin=True)
async def cmd_invite(message):
	await client.send_message(message.channel, f"https://discordapp.com/oauth2/authorize?&client_id={client.user.id}&scope=bot&permissions=0")

@commands.register("configure", admin=True)
async def cmd_configure(message):
	await upgrade_server_config(message.server.id)
	try:
		cmd, option, new = message.content.split(" ", 3)
	except:
		string = ""
		for x in serverconfig[message.server.id]["extra_options"]:
			string += f"**{x}**:**{serverconfig[message.server.id]['extra_options'][x]}** \n"
			await client.send_message(message.channel, string)
	else:
		if option in serverconfig[message.server.id]["extra_options"]:
			try:
				new = util.strtobool(new)
			except ValueError:
				await client.send_message(message.channel, "Invalid option.")
				return
			serverconfig[message.server.id]["extra_options"][option] = new
			await client.send_message(message.channel, f"Server option **{option}** has been set to **{new}**.")
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
	tagsraw.remove(f"{p}sankaku")	
	tags = " ".join(tagsraw)

	results, number_found = await get_content(session, 'span', "https://chan.sankakucomplex.com", attributes={"class":"thumb"}, params={"tags":tags, "commit":"Search"})
	if number_found == 0:
		await client.send_message(message.channel, f"No results found for `{tags.replace(' ',', ')}`.")
		return
	chosen = await get_random(number_found)
	pick = results[chosen-1].attrs['id'].replace("p","")
	
	image, number_found = await get_content(session, 'img', f"https://chan.sankakucomplex.com/post/show/{pick}", attributes={"id":"image"}, limit=1)
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
	tagsraw.remove(f"{p}gelbooru")	
	tags = " ".join(tagsraw)

	results, number_found = await get_content(session, 'span', "https://gelbooru.com/index.php?", attributes={"class":"thumb"}, params={"tags":tags, "page":"post","s":"list"})
	if number_found == 0:
		await client.send_message(message.channel, f"No results found for {tags.replace(' ',', ')}.")
		return
	chosen = await get_random(number_found)
	pick = results[chosen-1].attrs['id'].replace("s","")
	image, number_found = await get_content(session, 'img', f"https://gelbooru.com/index.php?", attributes={"id":"image"}, params={"page":"post", "s":"view", "id":pick}, limit=1)
	await client.send_message(message.channel, f'```Tags used: {tags.replace("+",", ")} \n https://gelbooru.com/index.php?page=post&s=view&id={pick}``` \n {image.attrs["src"]}')
	
	
	
	
@commands.register("nsfw", help="Enable or Disable NSFW in a channel.",admin=True)
async def cmd_nsfw(message):
	status = ""
	if message.channel.id in serverconfig[message.server.id]["nsfw_channels"]:
		status = "On"
	else:
		status = "Off"
	await client.send_message(message.channel, f"NSFW Status for channel **{message.channel.mention}** is **{status}**. Reply **on** to turn it on, **off** to turn it off, or **cancel** to cancel.")
	choice = await client.wait_for_message(author=message.author, timeout=30)
	if choice.content.lower() == "on":
		await client.send_message(message.channel, f"NSFW **Enabled** in **{message.channel.mention}**")
		if not message.channel.id in serverconfig[message.server.id]["nsfw_channels"]:
			serverconfig[message.server.id]["nsfw_channels"].add(message.channel.id)
	elif choice.content.lower() == "off":
		await client.send_message(message.channel, f"NSFW **Disabled** in **{message.channel.mention}**")
		if message.channel.id in serverconfig[message.server.id]["nsfw_channels"]:
			serverconfig[message.server.id]["nsfw_channels"].add(message.channel.id)
	else:
		await client.send_message(message.channel, "Operation cancelled.")
	save_server_config()


@commands.register("uinfo", help="Find various information about a user.", syntax="(userid or NONE)")
@handle_exceptions
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
	embd = await embed_gen(desc=f"**Name:** {usr.name}\n**Discriminator:** {usr.discriminator}\n**Account Creation Date:** {usr.created_at}\n**Nickname:** {usr.display_name}\n**Snowflake ID:** {usr.id}\n**Joined On:** {usr.joined_at}", type="info")
	await client.send_message(message.channel, embed=embd)
	
@commands.register("sinfo", help="Find information about the soerver the command is run in.")
async def cmd_sinfo(message):
	server = message.server
	embd = await embed_gen(desc=f"**Name:** {server.name}\n**Region:** {server.region}\n**Member Count:** {server.member_count}\n**Owner:** {server.owner.name}#{server.owner.discriminator}", type="info")
	await client.send_message(message.channel, embed=embd)	

@commands.register("servers", help="See all servers the bot is in.", bot_admin=True)
async def cmd_servers(message):
	string = ""
	for server in client.servers:
		string += f"{server.name} \n"
	embd = await embed_gen(title=f"Servers [{len(client.servers)}]", desc=string)
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
		await create_server_config(message.server.id)
	serverconfig[message.server.id]["log_channel"] = message.channel.id
	await client.send_message(message.channel, f"Log channel has been set to {message.channel.mention}")
	save_server_config()

@commands.register("8ball", help="Ask the all-seeing 8 ball a question.")
async def cmd_8ball(message):
	random_choices = ["It is certain.", "It is decidedly so.", "Without a doubt.", "Yes - definitely.", "You may rely on it.", "As I see it, yes.", "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.", "Reply hazy, try again", "Ask again later.", "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.", "Don't count on it.", "My reply is no.", "My sources say no", "Outlook not so good.", "Very doubtful."]
	choice = random.choice(random_choices)
	await client.send_message(message.channel, choice)

@commands.register("keys", help="Access functions relating to server keys.", syntax="(add|del|list|clear|help) (key or NONE)", admin=True)
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
			await create_server_config(message.server.id)
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
		string = ""
		for x in serverconfig[message.server.id]["keys"]:
			string += f"`{x}`, "
		await client.send_message(message.channel, string)
	elif option == "clear":
		serverconfig[message.server.id]["keys"] = set()
		await client.send_message(message.channel, "All server keys cleared.")
		save_server_config()
	elif option == None or option == "help":
		await client.send_message(message.channel, "Available options: `add`, `del`, `list`, `clear`, `help`") 
	
@commands.register("dbupdate", help="Update the server's data file. Useful if you're having issues with newer commands.", admin=True)
async def cmd_dbupdate(message):
	await upgrade_server_config(message.server.id)
	await client.send_message(message.channel, "The data file for this server has been updated.")

@commands.register("github", help="Provides a link to the github repo for the bot source code.")
async def cmd_github(message):
	await client.send_message(message.channel, "Here's a link to the Github repository for this bot: https://github.com/Brod8362/discord-bot")

async def find(message, term=None):	
	user = None
	if term:
		term = term.lower()
	if message.mentions != []:
		user = message.mentions[0]
	else:
		for member in message.server.members:
			if term in member.name.lower():
				user = member
				break
			elif term == member.id:
				user = member
				break
			elif not member.nick == None:
				if term.lower() in  member.nick.lower():
					user = member
					break
	if not user:
		return None
	return user

	
@commands.register("stats")
@handle_exceptions
async def cmd_stats(message):
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
	try:
		await client.send_message(message.channel, f"**Stats for {usr.name}**\n Messages Sent: {serverconfig[message.server.id]['user_stats'][usr.id]}")
	except KeyError:
		await client.send_message(message.channel, "No information found for that user.")

async def auto_save():
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
		await upgrade_server_config(x)
	logger.info("All server configs are up to date.")
	await auto_save()




client.run(config["token"])


