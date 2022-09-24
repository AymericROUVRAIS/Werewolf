# Libraries :
from random import *
from langage import langage
from discord.ext import commands
from discord.utils import get
import discord, asyncio, random




# Variables :
TOKEN = 'ODQwMjcwNDUxOTAxMDcxNDIw.YJVw1w.YAljYdEBwHuwkM4-D3pwgUW26p8'
werewolves_lair = 939937401772593285
answer_num = 0 # used for the class NumRole
game_on = True
roles_name = []
couple = []
roles = [
    (1, 'werewolf', 'werewolves'),
    (0, 'witch'),
    (0, 'seer'),
    (0, 'cupid'),
    (0, 'hunter')
] # 0 : only 1 player will have the role, 1 : bcp





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

def find_player(player, all_players):
    l = []
    if type(player) == list:
        for name, member in all_players:
            if player == name:
                l.append(name)
        return l
    else:
        for name, member in all_players:
            if player == name:
                return member

def find_role(name, role_list):
    for player, role in role_list:
        if player == name:
            return role

def find_max(l):
    return max(set(l), key = l.count)

def give_villager(n_role, n_player):
    l = []
    if n_role < n_player:
        villagers = n_player - n_role
        for i in range(villagers):
            l.append('villager')
    return l

def check_equality(players, players_role_list):
    l = []
    for player, member in players:
        for name, role in players_role_list:
            if player == name:
                l.append((member, role), )
    return l

def check_role(players, name):
    for player, role in players:
        if role == name:
            return player

def check_role_list(players, name):
    l = []
    for player, role in players:
        if role == name:
            l.append(player)
    return l

def check_same(players : list):
    for player1 in players:
        for player2 in players:
            if player1 == player2:
                return True
    return False

def check_exist(player, name_list):
    for name in name_list:
        if player == name:
            return True
    return False



# Classes :
class NumRole:
    def __init__(self):
        self.num = answer_num
    def content(self):
        return int(self.num)

class Kill:
    def __init__(self, all_players):
        self.all_players = all_players
        self.status = False
        self.name = ''
        self.role = ''
        self.player = None
        self.l = []

    def def_name(self, name):
        self.name = name
    
    def find_role(self):
        pass

    def def_player(self):
        for name, member in self.all_players:
            if self.name == name:
                self.player = member
    
    def ap_l(self, name):
        self.l.append(name)


class Witch(Kill):
    def __init__(self):
        Kill.__init__(self)
        self.status = ''
        self.status_s = False
        self.status_k = False

    def change_status(self, para):
        self.status = para