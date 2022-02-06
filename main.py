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

    
    # Define different reaction checks :
    def check(reaction, user):
        return user == ctx.message.author and msg.id == reaction.message.id and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')
    def check_msg(message):
        return message.author == ctx.message.author and ctx.message.channel == message.channel
    def check_answer(message):
        return message.author == ctx.author and message.guild is None



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
            return None

        # Check if enough players :
        elif num_player < 8 or num_player > 18:
            await ctx.channel.purge(limit=1)
            if num_player < 8:
                await ctx.send('Not enough players, there must be at least 8 players')
            if num_player > 18 :
                await ctx.send('Too many players, there must be less than 18 players')
            await ctx.send('The game can\'t start')
            return None

        elif check_same(players) == True:
            await ctx.send('The same player is being used multiple times')
            await ctx.send('The game will be cancelled')
            return None



        # Initializing the game :
        else:
            for player in players:
                channel = await player.create_dm()
                await channel.send('You have been added to a werewolf game!')

            
            for i in range(5): # define number of each role; 5 : number of role
                if roles[i][0] == 0:
                    msg = await ctx.send(f'Do you want a {roles[i][1]}?')
                    await msg.add_reaction('✅')
                    await msg.add_reaction('❌')

                    try:
                        reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
                    except asyncio.TimeoutError:
                        await ctx.send('Timeout, command no longer valid')

                    # If check, add the role to the list :
                    if reaction.emoji == '✅':
                        roles_name.append(roles[i][1])


                else: # werewolf, more if roles added
                    while int(answer_num.content) > num_player:
                        await ctx.send(f'How many {roles[i][2]} do you want? (0 - {num_player})')
                        answer_num = await client.wait_for('message', check=check_msg)
                        if int(answer_num.content) >= num_player:
                            await ctx.send('Too many players, please retype an input')
                    num_werewolf = int(answer_num.content)
                    if num_werewolf != 0:
                        for i in range(num_werewolf):
                            roles_name.append(roles[0][1]) # append "werewolf" to the list



    # Define new vars :
    num_role = count_num(roles_name) # numbers of roles except villagers
    roles_name.extend(give_villager(num_role, num_player)) # add villagers to the players left
    num_role = count_num(roles_name) # update num_role

    players_num_for_role = give_num(players_role_list, num_player) # give num to player
    role_num_to_give = give_num(roles_name, num_role)
    players_role_list = find_num(players_num_for_role, role_num_to_give, num_player)

    send_role = check_role(players, players_role_list)
    for p in send_role:
        channel = await p[0].create_dm()
        await channel.send(f'You are a {p[1]}')
    


    # Init role vars :
    werewolf = check_equality(send_role, 'werewolf')
    witch = check_equality(send_role, 'witch')
    seer = check_equality(send_role, 'seer')
    cupid = check_equality(send_role, 'cupid')
    hunter = check_equality(send_role, 'hunter')
    




    # TO DO :
    ##################################################################################################
    # Chanel for werewolves :                                                                        #
    # guild = ctx.guild                                                                              #
    # member = ctx.author                                                                            #
    # admin_role = get(guild.roles, name="Modo")                                                     #
    # werewolf= send_role[1][0]                                                                      #
    # overwrites = {                                                                                 #
    #     guild.default_role: discord.PermissionOverwrite(read_messages=False),                      #
    #     member: discord.PermissionOverwrite(read_messages=True),                                   #
    #     admin_role: discord.PermissionOverwrite(read_messages=True),                               #
    #     werewolf: discord.PermissionOverwrite(read_messages=True),                                 #
    # }                                                                                              #
    # channel = await guild.create_text_channel('werewolves-Lair', overwrites=overwrites)            #
    ##################################################################################################



    # Clean the channel for start :
    await ctx.channel.purge(limit=6)
    await ctx.send('A game has started !')




    # First night :
    night = 0
    await ctx.send('Cupid, wake up.')
    await cupid.send('Choose 2 player : ')
    msg = await client.wait_for('message', check=check_answer)



    # Main loop for the game
    game_on = True
    while game_on == True:
        # Night :
        await ctx.send(f'Night falls, it\'s the night #{night}')



        # Seer :
        await ctx.send('Seer, wake up.')
        channel = await seer.create_dm()
        await channel.send('You may pick a player to know his role.')

        # Werewolf :

        # Witch :

        night += 1
        break











# Run the bot :
client.run(TOKEN)