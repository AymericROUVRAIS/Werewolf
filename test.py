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
    answer_num = NumRole # number of x to add to the game
    answer_num.content = num_player+1

    roles_list = []
    for i in range(4):
        if roles[i][1] == 0:
            msg = await ctx.send(f'Do you want a {roles[i][0]}?')
            await msg.add_reaction('✅')
            await msg.add_reaction('❌')
            try:
                reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send('Timeout, command no longer valid')  
            if reaction.emoji == '✅':
                roles_list.append(roles[i][0])


        else: # werewolf, more if roles added
            while int(answer_num.content) > num_player:
                await ctx.send(f'How many {roles[i][0]} do you want? (0 - {num_player})')
                answer_num = await client.wait_for('message', check=check_msg)
                if int(answer_num.content) >= num_player:
                    await ctx.send('Too many players, please retype an input')
            num_werewolf = int(answer_num.content)
            if num_werewolf != 0:
                for i in range(num_werewolf):
                    roles_list.append(roles[0][0]) # append "werewolf" to the list


    num_role = count_num(roles_list) # numbers of roles except villagers
    players_role_list = [discord_members[i][0] for i in range(num_player)]



    # Add villagers to the players left :
    if num_role < num_player:
        villagers = num_player - num_role
        for i in range(villagers):
            roles_list.append('villager')
    num_role = count_num(roles_list) # update num_role

    # give number to players / roles :
    players_num_for_role = give_num(players_role_list, num_player)
    role_num_to_give = give_num(roles_list, num_role)

    
    for i in range(num_player):
        for x in range(num_player):
            if players_num_for_role[i][1] == role_num_to_give[x][1] : # if num ==, give role to player
                # players_role_list[i][0] = role_num_to_give[x][0]
                # not working str.replace not work, try str[i][o].replace
                pass
    await ctx.send(players_role_list)





# Run the bot
client.run(TOKEN)