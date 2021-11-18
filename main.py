from env import *

client = commands.Bot(command_prefix = '!')




# The bots events :
@client.event
async def on_ready():
    print('Ready!')








# Start command :
@client.command()
async def start(ctx, *players:discord.Member):
    # Variables :
    discord_members = members_list(players)
    num_player = count_num(players)
    answer_num = NumRole
    answer_num.content = num_player+1
    players_role_list = []
    for i in range(num_player):
        players_role_list.append(discord_members[i][0])

    # Define different reaction checks :
    def check(reaction, user):
        return user == ctx.message.author and msg.id == reaction.message.id and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')
    def check_msg(message):
        return message.author == ctx.message.author and ctx.message.channel == message.channel



    # Start message :
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

        elif num_player < 8 or num_player > 18:
            await ctx.channel.purge(limit=1)
            if num_player < 8:
                await ctx.send('Not enough players, there must be at least 8 players')
            if num_player > 18 :
                await ctx.send('Too many players, there must be less than 18 players')
            await ctx.send('The game can\'t start')




        # Main loop for the game :
        else:
            for player in players:
                channel = await player.create_dm()
                await channel.send('You have been added to a werewolf game!')

            
            for i in range(4): # define number of each role; 4 : number of role
                if roles[i][1] == 0:
                    msg = await ctx.send(f'Do you want a {roles[i][0]}?')
                    await msg.add_reaction('✅')
                    await msg.add_reaction('❌')
                    if reaction.emoji == '✅':
                        roles_name.append(roles[i][0])
                else:
                    while int(answer_num.content) > num_player-5 or int(answer_num.content) == 0:
                        await ctx.send(f'How many {roles[i][0]} do you want? (1 - {num_player})')
                        answer_num = await client.wait_for('message', check=check_msg)
                        if int(answer_num.content) >= num_player or int(answer_num.content) == 0:
                            await ctx.send('Too many players, please retype an input')
                    answer_num = give_num(answer_num.content)
                    for i in range(answer_num):
                        roles_name.append(roles[0][0]) # append "werewolf" to the list


            # affect roles to players :
            num_role = count_num(roles_name)
            players_num_for_role = give_num(players_role_list, num_player)
            role_num_to_give = give_num(roles_name, num_role)




@client.command()
async def make_channel(ctx):
    channel = await guild.create_text_channel('cool-channel')




# Run the bot :
client.run(TOKEN)