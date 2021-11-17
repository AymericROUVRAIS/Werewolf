# Libraries :
from discord.ext import commands
import discord, asyncio, random
from discord.utils import get
from random import *


# Variables :
TOKEN = ''
guild = '840268645996429343'
num_role = 0
num_total_roles = 4
roles_list = ['werewolf', 'witch', 'seer', 'cupid', 'hunter']
roles = [
    ('werewolve', 1),
    ('witch', 0),
    ('seer', 0),
    ('cupid', 0),
    ('hunter', 0)
    ] # 0 : only 1 player will have the role, 1 : 'indefinite'





# Functions :
def count_num(players):
    i = 0
    for player in players:
        i+=1
    return i

def members_tuple(players):
    a = ()
    for player in players:
        tuple(player)
        a += (player)
    return tuple(a)

def members_list(players):
    a = []
    for player in players:
        a.append((player.name, player),)
    return list(a)

def give_num(_list, max_num):
    a = random.sample(range(0, max_num), max_num)
    for i in range(max_num):
        _list.append((_list[i], a[i]))
    _list =  _list[max_num:]
    return _list



# Classes :
class NumRole:
    def __init__(self):
        self.num = num_role
    def content(self):
        return int(self.num)
