How to Run
==========

Required repositories
---------------------
discord.py
requests
bs4
PyYAML
Pillow

Installing repositories
-----------------------
You can install libraries on Linux with

`python3 -m pip install {library}`

on Windows, this will just be 

`python -m pip install {library}`

Public Bot
----------
If you don't feel like hosting the bot yourself but want it on your server, [I have a publicly hosted version.](https://discordapp.com/oauth2/authorize?&client_id=451526467596058625&scope=bot&permissions=0)


First time setup
----------------
Open up config_default.yaml with your preffered text editor. Here you can change some basic options for the bot.
Get your token and put it in the quotes after "token". You can also change the prefix here, by default it's b[ . 
If desired, you can specify a specific user to be the admin of the bot. By default, it automatically selects based 
on the owner of the bot token. After you've made your desired changes, rename the file to "config.yaml". 

Running the bot
---------------
Make sure you have all your repositories installed, and then run the bot under python3. Add it to a server and you should be ready to go.




Changing Code
=============
Being that this is github, there's nothing wrong with wanting to edit the code. All I can say is good luck, the code isn't
the neatest and will be horribly inefficient at times. (Some of the code in there is several months old.) However, I try 
to keep at least some level of documentation there. 


Bugs
====
Please document bugs with the bot in the issues section of the repository. I'll try my best to fix them when I can get around to it.

Planned Features and changes
============================
- Abliity to enable/disable commands
- Temporary Ban
- Consistent use of embeds
- Custom embed styles
- Consolidation of all watch key related commands into one command 
- Ability to "voice ban" people either indefinitely or for a given amount of time

