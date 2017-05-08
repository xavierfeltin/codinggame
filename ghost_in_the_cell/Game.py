class Game:
    '''
    Manage all the global states of the game
    '''


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

        self.ennemy_bomb_checked = [] #id of ennemy bomb checked during new input

        self.turn = 1

    def initialize_game(self, factory_count, link_count):
        '''
        Initialize the game at the beginning of the party
        :return:
        '''

        self.factory_count = factory_count
        self.link_count = link_count # the number of links between factories
        self.turn = 1

    def create_factories(self):
        for i in range(self.factory_count):
            self.factories.append(Factory(i))

    def add_link(self, factory_1, factory_2, distance):
        link = Link(i, self.factories[factory_1], self.factories[factory_2], distance)
        self.factories[factory_1].links[factory_2] = link
        self.factories[factory_2].links[factory_1] = link
        self.links.append(link)

    def reset(self):
        '''
        Rest the state of the game before getting the information of the new turn
        '''
        self.factories_owned.clear()
        self.factories_ennemy.clear()
        self.factories_targeted.clear()

        for factory in self.factories:
            factory.decrease_bombs()
            factory.restore_productivity()
            factory.reset_distances()
            factory.reset_orders()

    def initialize_factories(self):
        '''
        Initialize the state of the factories
        '''

        for factory in self.factories:
            factory.set_distances()
            factory.build_path()

    def process_input(self, entity_id, entity_type, arg_1, arg_2, arg_3, arg_4, arg_5):
        '''
        Manage the input from the game engine
        see documentation for arguments
        '''

        if entity_type == 'FACTORY':
            factory = self.factories[entity_id]
            factory.set_owner(arg_1)
            factory.stock = arg_2
            factory.set_production(arg_3, arg_4)

            if factory.owner == 1:
                self.factories_owned.append(factory)
            elif factory.owner == -1:
                self.factories_ennemy.append(factory)

        elif entity_type == 'TROOP':

            factory_origin = self.factories[arg_2]
            factory_destination = self.factories[arg_3]

            match_troop = [troop for troop in self.troops if troop.t_id == entity_id]
            if len(match_troop) == 0:
                new_troop = Troop(entity_id, arg_4, arg_5, arg_1, False, factory_origin.links[arg_3], factory_origin, factory_destination)

                self.troops.append(new_troop)
                factory_origin.sent_troops(arg_3, new_troop)

                if arg_1 == -1:
                    self.troops_ennemy.append(new_troop)
                else:  # same for player and neutral structure
                    self.troops_owned.append(new_troop)

            else:
                match_troop[0].eta = arg_5

        elif entity_type == 'BOMB':

            factory_origin = self.factories[arg_2]
            match_troop = [troop for troop in self.troops if troop.t_id == entity_id]

            if len(match_troop) == 0:
                if arg_1 == ENNEMY:
                    factory_destination = self.estimate_target(self.factories[arg_2])
                    link = factory_origin.links[factory_destination.f_id]
                else:
                    factory_destination = self.factories[arg_3]
                    link = factory_origin.links[arg_3]

                new_troop = Troop(entity_id, arg_4, arg_5, arg_1, True, link, factory_origin, factory_destination)

                def __init__(self, t_id, number, eta, owner, is_bomb, link, sender, destination):
                self.troops.append(new_troop)

                if arg_1 == -1:
                    self.troops_ennemy.append(new_troop)
                else:  # same for player and neutral structure
                    self.troops_owned.append(new_troop)
            else:
                if arg_1 == ENNEMY:
                    match_troop[0].eta -= 1
                else:
                    match_troop[0].eta = arg_4

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
        pass

    def send_orders_to_engine(self):
        msg = ''
        for factory in self.factories_owned:
            msg += factory.generate_message_orders()

        if len(self.factories_owned) > 0 :
            return msg[:-1]
        else:
            return 'WAIT'

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
            factory.solve_turn(self)

        #6) Check end conditions
        #TODO ?

        self.turn += 1

    def consolidate_inputs (self):
        for factory in self.factories:
            factory.set_distances()

    def solve_turn(self, simulated_game):
        for factory in self.factories_owned:
            factory.update_troops_after_moves()
            factory.emit_orders(simulated_game)

        #TODO : Post treatment to manage launching bombs
        #TODO : Post treatment to optimize orders

        print(self.send_orders_to_engine())
        self.turn += 1

    def next_id_troop(self):
        if len(self.troops) == 0:
            return 0
        else:
            return max(troop.t_id for troop in self.troops) + 1