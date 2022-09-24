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
    VoteWerewolf = Kill
    ChoiceWitch = Witch
    answer_num.content = num_player+1
    players_list = [discord_members[i][0] for i in range(num_player)]




    # Define different reaction checks :
    def check(reaction, user):
        return user == ctx.message.author and msg.id == reaction.message.id and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❌')
    def check_msg(message):
        return message.author == ctx.message.author and ctx.message.channel == message.channel

    def check_answer_werewolf(message):
        return message.author in werewolf and message.guild is None
    def check_answer_witch(message):
        return message.author == witch and message.guild is None
    def check_answer_seer(message):
        return message.author == seer and message.guild is None
    def  check_answer_cupid(message):
        return message.author == cupid and message.guild is None
    def check_answer_hunter(message):
        return message.author == hunter and message.guild is None
    def check_answer_villager(message):
        return message.author in villager and message.guild is None





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

    players_num_for_role = give_num(players_list, num_player) # give num to player
    role_num_to_give = give_num(roles_name, num_role)
    players_role_list = find_num(players_num_for_role, role_num_to_give, num_player)

    send_role = check_role(players, players_role_list)
    for p in send_role:
        channel = await p[0].create_dm()
        await channel.send(f'You are a {p[1]}')
    


    # Init role vars :
    werewolf = check_role(send_role, 'werewolf')
    witch = check_role(send_role, 'witch')
    seer = check_role(send_role, 'seer')
    cupid = check_role(send_role, 'cupid')
    hunter = check_role(send_role, 'hunter')
    villager = check_role(send_role, 'villager')
    mayor = ''




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









    ######################################################################################################################################################
    #                                                                                                                                                    #
    #                                                               Main Loop for the game                                                               #
    #                                                                                                                                                    #
    ######################################################################################################################################################






    night = 0
    game_on = True
    while game_on == True:
        # Night :
        await ctx.send(f'Night falls, it\'s the night #{night}')
        VoteWerewolf.all_players = discord_members # update list
        ChoiceWitch.all_players = discord_members


        # First night :
        if night == 0:
            #Cupid :
            await ctx.send('Cupid, wake up.')
            for i in range(2):
                if i == 0:
                    await cupid.send(f'Choose the {i+1}st player : ')
                else:
                    await cupid.send(f'Choose the {i+1}nd player : ')
                msg = await client.wait_for('message', check=check_answer_cupid)
                exist = check_exist(msg.content, players_list)
                couple.append(msg.content)
                while exist == False:
                    await cupid.send(f'Player {msg.content} does not exist, please try again')
                    msg = await client.wait_for('message', check=check_answer_cupid)
                    exist = check_exist(msg.content, players_list)
                    if exist == True:
                        couple.pop()
                        couple.append(msg.content)

            c1 = find_player(couple[0], discord_members)
            c2 = find_player(couple[1], discord_members)
            await c1.send(f'You are now bound to {couple[1]}')
            await c2.send(f'You are now bound to {couple[0]}')



        # Seer :
        await ctx.send('Seer, wake up.')
        await seer.send('You may pick a player to know his role.')
        msg = await client.wait_for('message', check=check_answer_seer)
        while check_exist(msg.content, players_list) == False:
            await seer.send(f'Player {msg.content} does not exist, please try again')
            msg = await client.wait_for('message', check=check_answer_seer)
        
        role = find_role(msg.content, players_role_list)
        await seer.send(f'{msg.content} is a {role}')



        # Werewolf :
        for w in werewolf:
            await w.send('Choose a victim.\nYou only have one answer, choose wisely')
            msg = await client.wait_for('message', check=check_answer_werewolf)
            VoteWerewolf.ap_l(msg.content)
            while check_exist(msg.content, players_list) == False:
                await w.send(f'Player {msg.content} does not exist, please try again')
                msg = await client.wait_for('message', check=check_answer_werewolf)
                VoteWerewolf.def_name(msg.content)

        VoteWerewolf.def_name(find_max(VoteWerewolf.l))
        VoteWerewolf.def_player()



        # Witch :
        if ChoiceWitch.status_k == False or ChoiceWitch.status_s == False:      # if both used, do nothing
            await ctx.send('Witch, wake up.')
            if ChoiceWitch.status_k == False and ChoiceWitch.status_s == False:                # both
                await witch.send('Do you want to kill or save a player or do nothing? K/S/N')
                msg = await client.wait_for('message', check=check_answer_witch)
                while msg.content != 'K' or msg.content != 'S' or msg.content != 'N':
                    await witch.send('Wrong input, please try again')
                    msg = await client.wait_for('message', check=check_answer_witch)
                ChoiceWitch.change_status(msg.content)

                if ChoiceWitch.status == 'K':
                    await witch.send('Who do you want to kill?')
                    msg = await client.wait_for('message', check=check_answer_witch)
                    while check_exist(msg.content, players_list) == False:
                        await witch.send(f'Player {msg.content} does not exist, please try again')
                        msg = await client.wait_for('message', check=check_answer_witch)
                    ChoiceWitch.status_k = False
                    ChoiceWitch.def_name(msg.content)
                    ChoiceWitch.def_player()

                elif ChoiceWitch.status == 'S':
                    await witch.send(f'{VoteWerewolf.name} has been choosen by the werewolves, do you want to save him? Y/N')
                    msg = await client.wait_for('message', check=check_answer_witch)
                    while msg.content != 'Y' or msg.contetn != 'N':
                        await witch.send('Wrong input, please try again')
                        msg = await client.wait_for('message', check=check_answer_witch)
                    if msg.content == 'Y':
                        ChoiceWitch.status_s = True




            elif ChoiceWitch.status_k == True:                                            # just kill 
                await witch.send('Do you want to kill a player? Y/N')
                msg = await client.wait_for('message', check=check_answer_witch)
                while msg.content != 'Y' or msg.content != 'N':
                    await witch.send('Wrong input, please try again')
                    msg = await client.wait_for('message', check=check_answer_witch)

                await witch.send('Who do you want to kill?')
                msg = await client.wait_for('message', check=check_answer_witch)
                while check_exist(msg.content, players_list) == False:
                    await witch.send(f'Player {msg.content} does not exist, please try again')
                    msg = await client.wait_for('message', check=check_answer_witch)

                ChoiceWitch.status_k = True
                ChoiceWitch.name = msg.content
                ChoiceWitch.find_player(discord_members)



            else :                                                        # just save
                await witch.send('Do you want to save a player? Y/N')
                msg = await client.wait_for('message', check=check_answer_witch)
                while msg.content != 'Y' or msg.content != 'N':
                    await witch.send('Wrong input, please try again')
                    msg = await client.wait_for('message', check=check_answer_witch)

                await witch.send(f'{VoteWerewolf.name} has been choosen by the werewolves, do you want to save him? Y/N')
                msg = await client.wait_for('message', check=check_answer_witch)
                while msg.content != 'Y' or msg.contetn != 'N':
                    await witch.send('Wrong input, please try again')
                    msg = await client.wait_for('message', check=check_answer_witch)
                if msg.content == 'Y':
                    ChoiceWitch.status_s = True







        # Day :
        await ctx.send('Everyone wake up')
        if ChoiceWitch.status_s == True:
            VoteWerewolf.status = False
        
        if ChoiceWitch.status_k == True and VoteWerewolf != None:
            await ctx.send('Two players died this night')
            await ctx.send(f'{ChoiceWitch.name} was a {ChoiceWitch.role} and {VoteWerewolf.name} was a {VoteWerewolf.role}')
            players_list.remove(ChoiceWitch.name)


        elif ChoiceWitch.status_k == True :
            await ctx.send('One player died this night')
            await ctx.send(f'{ChoiceWitch.name} was a {ChoiceWitch.role}')
        elif VoteWerewolf.status == True:
            await ctx.send('One player died this night')
            await ctx.send(f'{VoteWerewolf.name} was a {VoteWerewolf.role}')
        else :
            await ctx.send('No one died this night')

        if mayor == ChoiceWitch.name or mayor == VoteWerewolf.name:
            await ctx.send('The mayor is dead, a new one will be voted')
            mayor = None


        if night == 0 or mayor == None: # that or a on_message
            vote = []
            await ctx.send('Let\'s proceed to vote a mayor')
            await ctx.send('Votes will be done in dms, any incorrect name won\'t count')
            await ctx.send('You can debate here')

            msg = await client.wait_for('message', check=check_answer_witch)
            vote.append(msg.content)
            msg = await client.wait_for('message', check=check_answer_seer)
            vote.append(msg.content)
            msg = await client.wait_for('message', check=check_answer_cupid)
            vote.append(msg.content)
            msg = await client.wait_for('message', check=check_answer_hunter)
            vote.append(msg.content)
            for w in werewolf:
                msg = await client.wait_for('message', check=check_answer_werewolf)
                vote.append(msg.content)
            for v in villager:
                msg = await client.wait_for('message', check=check_answer_villager)
                vote.append(msg.content)

            vote = find_player(vote)
            mayor = find_max(vote)
            await ctx.send(f'The new mayor is : {mayor}')



            
        night += 1











# Run the bot :
client.run(TOKEN)