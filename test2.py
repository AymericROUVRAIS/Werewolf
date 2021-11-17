from env import *






def give_num(_list, max_num):
    a = random.sample(range(0, max_num), max_num)
    for i in range(max_num):
        _list.append((_list[i], a[i]))
    _list =  _list[16:]
    return _list





a = []
for i in range(16):
   b = 'a' + str(i)
   a.append(b)


players_num_for_role = give_num(a, 16)
print(players_num_for_role)


# a = random.sample(range(0, 16), 16)
# print(a)

# done = []
# a = 0
# for i in range(16):
#     a = randint(0, 17)
#     done.append(a)
#     while a in done[:i-1]:
#         a = randint(0, 17)