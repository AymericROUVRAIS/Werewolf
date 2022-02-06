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
    players_role_list = [discord_members[i][0] for i in range(num_player)]
    channel_w = client.get_channel(werewolves_lair)


    def check(message):
        return message.author == ctx.author and message.guild is None


    # Initializing the game :
    roles_name.append(roles[0][1]) # werewolf
    roles_name.append(roles[3][1]) # cupid

    # Define new vars :
    num_role = count_num(roles_name) # numbers of roles except villagers
    roles_name.extend(give_villager(num_role, num_player)) # add villagers to the players left
    num_role = count_num(roles_name) # update num_role

    players_num_for_role = give_num(players_role_list, num_player) # give num to player
    role_num_to_give = give_num(roles_name, num_role)
    players_role_list = find_num(players_num_for_role, role_num_to_give, num_player)

    send_role = check_role(players, players_role_list)
    for p in send_role:
        channel = await send_role[0][0].create_dm()
        await channel.send(f'{p[0]} is a {p[1]}')



    # Init role vars :
    werewolf = check_equality(send_role, 'werewolf')
    # witch = check_equality(send_role, 'witch')
    # seer = check_equality(send_role, 'seer')
    cupid = check_equality(send_role, 'cupid')
    # hunter = check_equality(send_role, 'hunter')




    # First night :
    await ctx.send('A game has started !')
    await ctx.send('Cupid, wake up.')
    await cupid.send('Choose 2 player : ')
    msg = await client.wait_for('message', check=check)
    




    # Main loop for the game
    while game_on == True:
        # Night :
        await ctx.send(f'Night falls')



        # Seer :
        # await ctx.send('Seer, wake up.')
        # await seer.send('You may pick a player to know his role.')

        # Werewolf :
        await channel_w.send('You may speak freely here')
        for w in werewolf:
            await w.send('Choose a victim.\nYou only have one answer, choose wisely')
            msg = await client.wait_for('message', check=check)
            print(msg)
            
        # Witch :


        break











# Run the bot :
client.run(TOKEN)











'''
[
    (<Member id=635422411294113792 name='Nain Féroce' discriminator='8583'
guild=<Guild id=840268645996429343 name='LoupGarou', 
'witch'), 
    (<Member id=850353152690487316 name='Lynfan' discriminator='9831' 
guild=<Guild id=840268645996429343 name='LoupGarou' , 
'werewolve')
]
'''