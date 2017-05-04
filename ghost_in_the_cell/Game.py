class Game:
    '''
    Manage all the global states of the game
    '''

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

    turn = 1

    @staticmethod
    def initialize_game(factory_count, link_count, matrix_links):
        '''
        Initialize the game at the beginning of the party
        :return:
        '''

        Game.factory_count = factory_count
        for i in range(factory_count):
            Game.factories.append(Factory(i))


        Game.link_count = link_count # the number of links between factories
        for raw_link in link_count:
            factory_1, factory_2, distance = raw_link
            link = Link(i, Game.factories[factory_1], Game.factories[factory_2], distance)
            Game.factories[factory_1].links[factory_2] = link
            Game.factories[factory_2].links[factory_1] = link
            Game.links.append(link)

        Game.initialize_factories()

        Game.turn = 1

    @staticmethod
    def initialize_factories():
        '''
        Initialize the state of the factories
        '''

        for factory in Game.factories:
            factory.set_distances()
            factory.build_path()
            factory.initialize_nb_cyborgs_coming()

    @staticmethod
    def estimate_target(origin):
        '''
        Choose the possible target of the ennemy bomb and set the bomb eta accordingly
        '''

        if Game.turn == 1:
            target = Game.factories_owned[0]
            eta = origin.links[target.f_id].distance - 1
        else:
            temp = sorted(Game.factories_owned, key=lambda factory: (-factory.bomb_eta, -factory.production, -factory.stock, origin.links[factory.f_id].distance))
            target = temp[0]
            eta = origin.links[target.f_id].distance - 1

        target.set_bomb_eta(eta)
        return target

    @staticmethod
    def check_ennemy_bombs():
        '''
        Update the ennemy bombs on their potential target
        '''
        for target in Game.ennemy_bombs:
            if target is not None and target.bomb_eta == -1:
                target = None

    @staticmethod
    def send_orders_to_engine(self):
        msg = ''
        for factory in self.factories_owned:
            msg += factory.generate_message_orders()

        return msg[:-1]

    @staticmethod
    def simulate_turn():
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
        for link in Game.links:
            link.move_troops()

        #2) Execute user orders
        #3) Produce new cyborgs in all factories
        #4) Solve battles
        #5) Make the bombs explode
        for factory in Game.factories:
            factory.update_troops_after_moves()
            factory.solve_turn()

        #6) Check end conditions
        #TODO ?

    @staticmethod
    def next_id_troop():
        return max(troop.t_id for troop in Game.troops) + 1