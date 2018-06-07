#!/bin/usr/python3
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
nsfw_enabled = set()



#log stuff
logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s', level=logging.INFO)
logger = logging.getLogger("test-bot")


config = {}
#reading configs
with open("config.yaml", "r") as stream:
	config = (yaml.load(stream))
		
 
p = config["prefix"]
adminid = config["adminid"]

#loading NSFW values into set 
for line in open('nsfw_list'):
	nsfw_enabled.add(line.strip())

#loading opus for voice functionality
if not discord.opus.is_loaded():
	logger.info("opus dll not loaded, loading now")
	opusdll="C:/Users/Blake/Documents/Actual Documents/discord.py-async/discord/bin/libopus-0.x64.dll" #path to opus dll
	dicord.opus.load_opus(opusdll)
	logger.info("opsu dll loaded successfully.")

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
		if admin and self.admin[name]: #for admin commands
			return self.help[name]+" **[ADMIN]**"
		elif not self.admin[name] and not self.sadmin[name]: #regular commands
			return self.help[name]
		elif await check_bot_admin(user): #superadmin commands
			return self.help[name]+" **[BOT ADMIN]**"
		else:
			return None
	
	def get_syntax(self, name):
		return self.syntax[name]

commands = CommandRegistry(p) #this is the prefix 


@client.event
async def on_message(message):
	if message.author.bot:
		return
	elif message.content.startswith(".. "):
		cmd, key, content = message.content.split(" ", 2)
		embd = await embed_gen(title="Quote Created", desc=f"**{message.author.mention}** created quote **{key}** with content **{content}**", color=0x000000, author=message.author, footer_author=True, footer_author_id=True)
		channelset = message.server.get_channel("277384105245802497")
		await client.send_message(channelset, embed=embd)
	elif message.content.startswith(".qdel "):
		confirmation = await client.wait_for_message(author=await get_user("116275390695079945"))
		if "deleted." in confirmation.embeds[0]["description"]:
			cmd, id, = message.content.split(" ", 1)
			embd = await embed_gen(title="Quote Deleted", desc=f"**{message.author.mention}** deleted quote **{id}**", color=0xFF0000, author=message.author, footer_author=True, footer_author_id=True)
			channelset = message.server.get_channel("277384105245802497")
			await client.send_message(channelset, embed=embd)
	try:
		cmd = commands.get(message.content.split()[0])
	except IndexError:
		return
	if cmd:
		await cmd(message)
		

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
	if str(message.author.id) == f"{adminid}":
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
			embd = await embed_gen(desc="Forceful shutdown.", type="info")
			await client.send_message(message.channel, embed = embd)
			await client.close()
			sys.exit()
			return
	else: 
		logger.info(f"attempted shut down by {message.author} in {message.server.name}")
		embd = await embed_gen(title="\U0001F6AB No Permission", desc=f"Only unknown can do that.", color=0xFF0000, author=message.author)
		await client.send_message(message.channel, embed=embd)

@commands.register("invite", help="Creates an invite link for the bot.", syntax=f"", bot_admin=True)
async def cmd_invite(message):
	if not await check_bot_admin(message.author):
		return
	await client.send_message(message.channel, f"https://discordapp.com/oauth2/authorize?&client_id={client.user.id}&scope=bot&permissions=0")

@commands.register("configure", admin=True)
async def cmd_configure(message):
	if not await check_admin(message.author):
		return
	await client.send_message(message.channel, "Work in progress.")
	
@commands.register("sankaku", help="Retrieves image(s) from Sankaku using specified tags.", syntax=f"(tags)")
async def cmd_sankaku(message):
	if message.channel.id not in nsfw_enabled:
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
	if message.channel.id not in nsfw_enabled:
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
	if not await check_admin(message.author):
		return
	if message.channel.id in nsfw_enabled:
		status = "On"
	else:
		status = "Off"
	await client.send_message(message.channel, f"NSFW Status for channel **{message.channel.mention}** is **{status}**. Reply **on** to turn it on, **off** to turn it off, or **cancel** to cancel.")
	choice = await client.wait_for_message(author=message.author, timeout=30)
	if choice.content.lower() == "on":
		nsfw_enabled.add(message.channel.id)
		await client.send_message(message.channel, f"NSFW **Enabled** in **{message.channel.mention}**")
	elif choice.content.lower() == "off":
		nsfw_enabled.remove(message.channel.id)
		await client.send_message(message.channel, f"NSFW **Disabled** in **{message.channel.mention}**")
	else:
		await client.send_message(message.channel, "Operation cancelled.")
	file = open("nsfw_list", "w")
	for x in nsfw_enabled:
		file.write(f"{x}\n")
	
@commands.register("uinfo", help="Find various information about a user.", syntax="(userid or NONE)")
async def cmd_uinfo(message):
	try:
		command, msg = message.content.split(" ", 1)
	except ValueError:
		usr = message.author
	else:
		try:
			usr = await get_user(msg)
		except:
			print("exception happened")
		else:
			pass
	if not message.mentions == []:
		usr = message.mentions[0]
	embd = await embed_gen(desc=f"**Name:** {usr.name}\n**Discriminator:** {usr.discriminator}\n**Account Creation Date:** {usr.created_at}\n**Nickname:** {usr.display_name}\n**Snowflake ID:** {usr.id}\n**Joined On:** {usr.joined_at}", type="info")
	await client.send_message(message.channel, embed=embd)
	
@commands.register("sinfo", help="Find information about the server the command is run in.")
async def cmd_sinfo(message):
	server = message.server
	embd = await embed_gen(desc=f"**Name:** {server.name}\n**Region:** {server.region}\n**Member Count:** {server.member_count}\n**Owner:** {server.owner.name}#{server.owner.discriminator}", type="info")
	await client.send_message(message.channel, embed=embd)	

@commands.register("servers", help="See all servers the bot is in.", bot_admin=True)
async def cmd_servers(message):
	if not await check_bot_admin(message.author):
		return
	string = ""
	for server in client.servers:
		string += f"{server.name} \n"
	embd = await embed_gen(title=f"Servers [{len(client.servers)}]", desc=string)
#footer_content=f"{str(len(client.servers))} servers",footer_icon_url=None)
	await client.send_message(message.channel, embed=embd)
	
@commands.register("sosad", help="Quickly make a 'so sad' meme.")
async def cmd_sosad(message):
	try:
		sourceurl = message.attachments[0]["url"]
	except IndexError:
		await client.send_message(message.channel, "An image could not be found. Make sure it's attached to your message, and isn't a link to an image.")
		return
	sourcedimensions = (message.attachments[0]["width"], message.attachments[0]["height"])
	source = requests.get(sourceurl)
	source = io.BytesIO(source.content)
	source = Image.open(source)
	sosad = Image.open("resources/sosad.jpg")
	ratio = sosad.height/sosad.width
	sosad = sosad.resize((source.width, math.ceil(source.width*ratio)))
	new_size = (source.width, source.height+sosad.height)
	newimage = Image.new("RGB", new_size)
	newimage.paste(source)
	newimage.paste(sosad, (0, source.height))
	newimage.save("resources/temp.jpg")
	await client.send_file(message.channel, fp="resources/temp.jpg", content="This is ***SO SAD*** can we hit ***50*** likes?!??!")
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
		return





client.run(config["token"])


