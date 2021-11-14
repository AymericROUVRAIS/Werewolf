from env import *

client = commands.Bot(command_prefix = '!')




# The bots events :
@client.event
async def on_ready():
    print('Ready!')



# Functions
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

num_role = 0
class Python_con:
    def __init__(self):
        self.num = num_role
    def content(self):
        return int(self.num)




# Start command :
@client.command()
async def start(ctx, *players):
    def check_msg(message):
        return message.author == ctx.message.author and ctx.message.channel == message.channel

    discord_members = members_tuple(players)

    num_player = count_num(players)
    num_role = Python_con
    num_role.content = num_player+1
    for i in range(4):
        if roles[i][1] == 0:
            msg = await ctx.send(f'Do you want a {roles[i][0]}?')
            await msg.add_reaction('✅')
            await msg.add_reaction('❌')
        else:
            while int(num_role.content) >= num_player:
                await ctx.send(f'How many {roles[i][0]} do you want? (0 - {num_player})')
                num_role = await client.wait_for('message', check=check_msg)
                if int(num_role.content) >= num_player:
                    await ctx.send('Too many players, please retype an input')

    await ctx.send(discord_members)





# run the bot
client.run(TOKEN)