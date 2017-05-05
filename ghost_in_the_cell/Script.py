


factories = []
factories_owned = []
factories_ennemy = []
factories_targeted = []

links = []

troops = []
troops_owned = []
troops_ennemy = []

ennemy_bombs = [None, None]
ennemy_bomb = False  # True if an ennemy bomb is currently moving
available_bomb = 2

# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.
factory_count = int(input())  # the number of factories
for i in range(factory_count):
    factories.append(Factory(i))

link_count = int(input())  # the number of links between factories
for i in range(link_count):
    factory_1, factory_2, distance = [int(j) for j in input().split()]
    link = Link(i, factories[factory_1], factories[factory_2], distance)
    factories[factory_1].links[factory_2] = link
    factories[factory_2].links[factory_1] = link
    links.append(link)

for factory in factories:
    factory.set_distances()
    factory.build_path()
    factory.initialize_nb_cyborgs_coming()

turn = 1

# game loop
while True:
    factories_owned.clear()
    factories_ennemy.clear()
    factories_targeted.clear()

    for factory in factories:
        factory.reset_cyborgs()
        factory.decrease_bombs()
        factory.restore_productivity()
        factory.reset_distances()

    check_ennemy_bombs()

    ennemy_bomb = False
    nb_bomb_ennemy = 0

    # factories.sort(key=attrgetter('f_id'))
    troops.sort(key=attrgetter('t_id'))

    entity_count = int(input())  # the number of entities (e.g. factories and troops)
    for i in range(entity_count):
        entity_id, entity_type, arg_1, arg_2, arg_3, arg_4, arg_5 = input().split()
        entity_id = int(entity_id)
        arg_1 = int(arg_1)
        arg_2 = int(arg_2)
        arg_3 = int(arg_3)
        arg_4 = int(arg_4)
        arg_5 = int(arg_5)

        if entity_type == 'FACTORY':
            factory = factories[entity_id]
            factory.set_owner(arg_1)
            factory.stock = arg_2
            factory.set_production(arg_3, arg_4)

            if factory.owner == 1:
                factories_owned.append(factory)
            elif factory.owner == -1:
                factories_ennemy.append(factory)

        elif entity_type == 'TROOP':

            factory_origin = factories[arg_2]
            factory_destination = factories[arg_3]

            match_troop = [troop for troop in troops if troop.t_id == entity_id]
            if len(match_troop) == 0:
                new_troop = Troop(entity_id, arg_4, arg_5, arg_1, False, factory_origin.links[arg_3], factory_origin, factory_destination)

                troops.append(new_troop)
                factory_origin.sent_troops(arg_3, new_troop)
                factory_destination.add_coming_cyborgs(new_troop)

                if arg_1 == -1:
                    troops_ennemy.append(new_troop)
                else:  # same for player and neutral structure
                    troops_owned.append(new_troop)

            else:
                match_troop[0].eta = arg_5

                if arg_1 == -1:
                    if factory_destination.owner == -1:
                        factory_destination.cyborgs_coming[FRIEND][arg_5 - 1] += arg_4
                    else:
                        factory_destination.cyborgs_coming[ENNEMY][arg_5 - 1] += arg_4
                else:  # same for player and neutral structure
                    if factory_destination.owner == -1:
                        factory_destination.cyborgs_coming[ENNEMY][arg_5 - 1] += arg_4
                    else:
                        factory_destination.cyborgs_coming[FRIEND][arg_5 - 1] += arg_4

        elif entity_type == 'BOMB':
            if arg_1 == -1:

                if ennemy_bombs[nb_bomb_ennemy] is None:
                    ennemy_bombs[nb_bomb_ennemy] = estimate_target(factories[arg_2])

                    print('bomb : ' + str(ennemy_bombs[nb_bomb_ennemy].f_id) + ', eta = ' + str(ennemy_bombs[nb_bomb_ennemy].bomb_eta), file=sys.stderr)

                nb_bomb_ennemy += 1

            else:
                factories[arg_3].set_bomb_eta(arg_4)

    # Consolidation of the provided data
    for factory in factories:
        factory.set_distances()

    for link in links:
        link.define_conquest_priorities()

    for factory in factories:
        for key, pathes in factory.alternative_pathes.items():
            for path in pathes:
                path.define_conquest_priority()

    message = ''
    factories_owned.sort(key=attrgetter('current_production'))
    for factory in factories_owned:

        factory_message = factory.emit_orders()
        if factory_message != '':
            if message != '':
                message += ';'
            message += factory_message
            if factory_message[0] != '' and factory_message[0] == 'B':
                available_bomb -= 1

    # TODO add message for comparing production of two players
    if len(message) == 0:
        print("WAIT")
    else:
        print(message)

    turn += 1