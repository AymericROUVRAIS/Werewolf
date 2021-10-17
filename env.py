# libraries :
from discord.ext import commands
import discord, asyncio, random
from discord.utils import get
from discord_components import DiscordComponents, Button, ButtonStyle, component



# variables :
TOKEN = ''
guild = '840268645996429343'
roles = [
    ('werewolves', 1),
    ('witch', 0),
    ('seer', 0),
    ('cupid', 0),
    ('hunter', 0)
    ] # 0 : only 1 player will have the role, 1 : 'indefinite'
