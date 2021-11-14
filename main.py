from env import *

client = commands.Bot(command_prefix = '!')




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
        a += (player.name, player)
    return tuple(a)

class NumRole:
    def __init__(self):
        self.num = num_role
    def content(self):
        return int(self.num)




# Start command :
@client.command()
async def start(ctx, *players:discord.Member):
    num_player = count_num(players)
    num_role = NumRole
    num_role.content = num_player+1
    
    # Define different checks
    def check(reaction, user):
        return user == ctx.message.author and msg.id == reaction.message.id and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')
    def check_msg(message):
        return message.author == ctx.message.author and ctx.message.channel == message.channel

    # Start message
    msg = await ctx.send('You\'re about to start a werewolf game\nAre you sure?')
    await msg.add_reaction('✅')
    await msg.add_reaction('❌')

    try:
        reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send('Timeout, command no longer valid')  
    else:
        if reaction.emoji == '❌':
            await ctx.channel.purge(limit=1)
            await ctx.send('The game has been cancelled')

        # elif num_player < 8 or num_player > 18:
        #     await ctx.channel.purge(limit=1)
        #     if num_player < 8:
        #         await ctx.send('Not enough players, there must be at least 8 players')
        #     if num_player > 18 :
        #         await ctx.send('Too many players, there must be less than 18 players')
        #     await ctx.send('The game can\'t start')




        # Main loop for the game
        else:
            discord_members = members_tuple(players)
            await ctx.send(discord_members)

            for player in players:
                channel = await player.create_dm()
                await channel.send('You have been added to a werewolf game!')

            
            for i in range(num_total_roles): # define number of each role
                if roles[i][1] == 0:
                    msg = await ctx.send(f'Do you want a {roles[i][0]}')
                    await msg.add_reaction('✅')
                    await msg.add_reaction('❌')
                    if reaction.emoji == '✅':
                        pass
                else:
                    while int(num_role.content) > num_player:
                        await ctx.send(f'How many {roles[i][0]} do you want? (0 - {num_player})')
                        num_role = await client.wait_for('message', check=check_msg)
                        if int(num_role.content) >= num_player:
                            await ctx.send('Too many players, please retype an input')
                    
            # affect roles to players

  


@client.command()
async def make_channel(ctx):
    channel = await guild.create_text_channel('cool-channel')



# run the bot
client.run(TOKEN)