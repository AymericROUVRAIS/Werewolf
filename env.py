# Libraries :
from random import *
from langage import langage
from discord.ext import commands
from discord.utils import get
import discord, asyncio, random




# Variables :
TOKEN = ''
guild = '840268645996429343' # number of the guild the bot is in : "LoupGarou"
werewolves_lair = 939937401772593285
answer_num = 0 # used for the class NumRole
game_on = True
roles_name = []
roles = [
    (1, 'werewolf', 'werewolves'),
    (0, 'witch'),
    (0, 'seer'),
    (0, 'cupid'),
    (0, 'hunter')
] # 0 : only 1 player will have the role, 1 : 'indefinite'





# Functions :
def count_num(l : list):
    i = 0
    for item in l:
        i+=1
    return i

def members_list(players):
    a = []
    for player in players:
        a.append((player.name, player),)
    return list(a)

def give_num(l : list, max_num):
    a = random.sample(range(0, max_num), max_num)
    for i in range(max_num):
        l.append([l[i], a[i]])
    l = l[max_num:]
    return l

def find_num(l1, l2, max_num):
    l = []
    for i in range(max_num):
        for j in range(max_num):
            if l1[i][1] == l2[j][1]:
                l.append([l1[i][0], l2[j][0]])
    return l

def give_villager(n_role, n_player):
    l = []
    if n_role < n_player:
        villagers = n_player - n_role
        for i in range(villagers):
            l.append('villager')
    return l

def check_role(players, players_role_list):
    l = []
    for player in players:
        for name, role in players_role_list:
            player1 = str(player)
            if player1[:-5] == name:
                l.append((player, role), )
    return l

def check_equality(players, name):
    l = []
    for player, role in players:
        if role == name:
            l.append(player)
        print(player)
    return l

def check_same(players : list):
    for player1 in players:
        for player2 in players:
            if player1 == player2:
                return True
    return False

def check_exist():
    pass



# Classes :
class NumRole:
    def __init__(self):
        self.num = answer_num
    def content(self):
        return int(self.num)
