class Game:
    '''
    Manage all the global states of the game
    '''

    real = None
    simulated = None

    def __init__(self):
        if not Game.real:
            Game.real = Game.__Game()

        if not Game.simulated:
            Game.simulated = Game.__Game()

    class __Game:
        def __init__(self):
            self.factories = []
            self.factories_owned = []
            self.factories_ennemy = []
            self.factories_targeted = []

            self.links = []

            self.troops = []
            self.troops_owned = []
            self.troops_ennemy = []

            self.ennemy_bombs = [None, None]
            self.ennemy_bomb = False  # True if an ennemy bomb is currently moving
            self.available_bomb = 2

            self.turn = 1

        def initialize_game(self, factory_count, link_count, matrix_links):
            '''
            Initialize the game at the beginning of the party
            :return:
            '''

            self.factory_count = factory_count
            for i in range(factory_count):
                self.factories.append(Factory(i))


            self.link_count = link_count # the number of links between factories
            for raw_link in link_count:
                factory_1, factory_2, distance = raw_link
                link = Link(i, self.factories[factory_1], self.factories[factory_2], distance)
                self.factories[factory_1].links[factory_2] = link
                self.factories[factory_2].links[factory_1] = link
                self.links.append(link)

            self.initialize_factories()

            self.turn = 1

        def initialize_factories(self):
            '''
            Initialize the state of the factories
            '''

            for factory in self.factories:
                factory.set_distances()
                factory.build_path()
                factory.initialize_nb_cyborgs_coming()

        def estimate_target(self, origin):
            '''
            Choose the possible target of the ennemy bomb and set the bomb eta accordingly
            '''

            if self.turn == 1:
                target = self.factories_owned[0]
                eta = origin.links[target.f_id].distance - 1
            else:
                temp = sorted(self.factories_owned, key=lambda factory: (-factory.bomb_eta, -factory.production, -factory.stock, origin.links[factory.f_id].distance))
                target = temp[0]
                eta = origin.links[target.f_id].distance - 1

            target.set_bomb_eta(eta)
            return target

        def check_ennemy_bombs(self):
            '''
            Update the ennemy bombs on their potential target
            '''
            for target in self.ennemy_bombs:
                if target is not None and target.bomb_eta == -1:
                    target = None

        def send_bomb_order(self, link, fact_destination):
            '''
            Manage to send a bomb if possible
            '''

            #TODO: manage bomb function of the global state of the game
            '''
            nb_cyborg_player = self.nb_friendly_troops
            nb_cyborg_ennemy = self.nb_ennemy_troops

            estimated_stock = fact_destination.get_estimated_stock(NB_PREDICTED_TURN_BOMB - self.count_zero_prod)

            evaluated_defense = nb_cyborg_ennemy + estimated_stock
            nb_defense_left = evaluated_defense - nb_cyborg_player

            return fact_destination.owner == -1 and link.distance <= MAX_BOMB_DISTANCE and nb_defense_left >= MIN_DEFENSE_TO_SEND_BOMB and (
            fact_destination.current_production >= 2 \
            or len(Game.factories_ennemy) == 1) and fact_destination.bomb_eta == -1 and Game.available_bomb != 0
            '''

        def send_orders_to_engine(self):
            msg = ''
            for factory in self.factories_owned:
                msg += factory.generate_message_orders()

            return msg[:-1]

        def simulate_turn(self):
            '''
            Simulate one full turn for all the factories
            1) Move existing troops and bombs
            2) Execute user orders
            3) Produce new cyborgs in all factories
            4) Solve battles
            5) Make the bombs explode
            6) Check end conditions
            '''

            #1) Move existing troops and bombs
            for link in self.links:
                link.move_troops()

            #2) Execute user orders
            #3) Produce new cyborgs in all factories
            #4) Solve battles
            #5) Make the bombs explode
            for factory in self.factories:
                factory.update_troops_after_moves()
                factory.solve_turn()

            #6) Check end conditions
            #TODO ?

        def next_id_troop(self):
            return max(troop.t_id for troop in self.troops) + 1