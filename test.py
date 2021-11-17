from env import *

client = commands.Bot(command_prefix = '!')




# The bots events :
@client.event
async def on_ready():
    print('Ready!')





# Start command :
@client.command()
async def start(ctx, *players:discord.Member):
    # Define different checks
    def check(reaction, user):
        return user == ctx.message.author and msg.id == reaction.message.id and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')
    def check_msg(message):
        return message.author == ctx.message.author and ctx.message.channel == message.channel

    discord_members = members_list(players)

    num_player = count_num(players)
    num_role = NumRole
    num_role.content = num_player+1
    for i in range(4):
        if roles[i][1] == 0:
            msg = await ctx.send(f'Do you want a {roles[i][0]}?')
            await msg.add_reaction('✅')
            await msg.add_reaction('❌')
            try:
                reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send('Timeout, command no longer valid')  
            if reaction.emoji == '❌':
                pass

        else:
            while int(num_role.content) > num_player:
                await ctx.send(f'How many {roles[i][0]} do you want? (0 - {num_player})')
                num_role = await client.wait_for('message', check=check_msg)
                if int(num_role.content) >= num_player:
                    await ctx.send('Too many players, please retype an input')


    players_role_list = []
    for i in range(num_player):
        players_role_list.append(discord_members[i][0])


    players_num_for_role = give_num(players_role_list, num_player)
    role_num = give_num(roles_list, 4)

    await ctx.send(players_num_for_role)
    await ctx.send(role_num)

    for i in range(num_player):
        for x in range(num_player):
            if i == x : # if num ==, give role to player
                pass




# Run the bot
client.run(TOKEN)