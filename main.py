import random
import discord, asyncio
from discord.ext import commands

client = commands.Bot(command_prefix = '/')





# The bots events :
@client.event
async def on_ready():
    print('Ready!')




# Different functions for game :
NAME = 0
MEMBER = 1

def count_num(players):
    i = 0
    for player in players:
        i+=1
    return i

def members_tuple(players):
    a = ()
    for player in players:
        a.append([player.name, players])
    return tuple(a)








# Start command :
@client.command()
async def start(ctx, *players:discord.Member):
    def check(reaction, user):
        return user == ctx.message.author and msg.id == reaction.message.id and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')

    msg = await ctx.send('You\'re about to start a werewolf game\nAre you sure?')
    await msg.add_reaction('✅')
    await msg.add_reaction('❌')

    num_player = count_num(players)    

    try:
        reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send('Timeout, command no longer valid')
    else:
        if reaction.emoji == '❌':
            await ctx.channel.purge(limit=1)
            await ctx.send('The game has been cancelled')

        elif num_player < 8 or num_player > 18:
            await ctx.purge(limit=1)
            await ctx.send('Too many players, there must be 8 to 18 players')
            await ctx.send('The game can\'t start')




        # Main loop for the game
        else:
            discord_members = members_tuple(players)

            for player in players:
                channel = await player.create_dm()
                await channel.send('You have been added to a werewolf game!')

            





# run the bot
client.run('')
