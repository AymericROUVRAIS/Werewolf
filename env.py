# libraries :
from discord.ext import commands
import discord, asyncio, random
from discord.utils import get



# variables :
TOKEN = ''
guild = '840268645996429343'
num_role = 0
num_total_roles = 4
roles = [
    ('werewolve', 1),
    ('witch', 0),
    ('seer', 0),
    ('cupid', 0),
    ('hunter', 0)
    ] # 0 : only 1 player will have the role, 1 : 'indefinite'
