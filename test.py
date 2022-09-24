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
    players_list = [discord_members[i][0] for i in range(num_player)]



    VoteWerewolf = Kill
    ChoiceWitch = Witch



    def check(message):
        return message.author == ctx.author and message.guild is None


    # Initializing the game :
    roles_name.append(roles[2][1]) # cupid
    roles_name.append(roles[1][1]) # witch

    # Define new vars :
    num_role = count_num(roles_name) # numbers of roles
    players_num_for_role = give_num(players_list, num_player) # give num to player
    role_num_to_give = give_num(roles_name, num_role)
    players_role_list = find_num(players_num_for_role, role_num_to_give, num_player)


    send_role = check_equality(discord_members, players_role_list)
    for p in send_role:
        channel = await send_role[0][0].create_dm()
        await channel.send(f'{p[0]} is a {p[1]}')



    # Init role vars :
    werewolf = check_role_list(send_role, 'werewolf')
    witch = check_role(send_role, 'witch')
    # seer = check_role(send_role, 'seer')
    # cupid = check_role(send_role, 'cupid')
    # hunter = check_role(send_role, 'hunter')



    # Witch :
    await ctx.send('Seer, wake up.')
    await witch.send('Do you want to kill or save a player? K/S')
    msg = await client.wait_for('message', check=check)
    while msg.content != 'K' or msg.content != 'S':
        await witch.send('Wrong input, please try again')
        msg = await client.wait_for('message', check=check)

    if msg.content == 'K':
        await witch.send('Who do you want to kill?')
        msg = await client.wait_for('message', check=check)
        exist = check_exist(msg.content, players_list)
        while exist == False:
            await witch.send(f'Player {msg.content} does not exist, please try again')
            msg = await client.wait_for('message', check=check)
            exist = check_exist(msg.content, players_list)
        kill = find_player(msg.content, discord_members)

    else:
        await witch.send('Who do you want to save?')
        msg = await client.wait_for('message', check=check)
        exist = check_exist(msg.content, players_list)
        while exist == False:
            await witch.send(f'Player {msg.content} does not exist, please try again')
            msg = await client.wait_for('message', check=check)
            exist = check_exist(msg.content, players_list)
        save = find_player(msg.content, discord_members)















# Run the bot :
client.run(TOKEN)







# Discord members : [('Nain Féroce', <Member id=635422411294113792 name='Nain Féroce' discriminator='8583' bot=False nick=None guild=<Guild id=840268645996429343 name='LoupGarou' shard_id=None chunked=False member_count=9>>), ('Lynfan', <Member id=850353152690487316 name='Lynfan' discriminator='9831' bot=False nick=None guild=<Guild id=840268645996429343 name='LoupGarou' shard_id=None chunked=False member_count=9>>)]
# Players list : ['Nain Féroce', 'Lynfan']
# Player role list : [['Nain Féroce', 'werewolf'], ['Lynfan', 'cupid']]