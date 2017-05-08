import sys
import math
from operator import attrgetter

FRIEND = 1
PLAYER = 1
ENNEMY = -1
NEUTRAL = 0
NEUTRAL_2 = 2

NB_CYBORG_INC = 10
DELTA_CONQUER = 1
FIRST_EXPLORATION_DELTA = 5

MAX_BOMB_DISTANCE = 5
MIN_DEFENSE_TO_SEND_BOMB = 5

COUNT_INCREASE = 0

MIN_FACTORY_CONSIDERED = 6
MAX_DISTANCE_CONSIDERED = 4
NB_PREDICTED_TURN = 3
NB_PREDICTED_TURN_BOMB = 5

NB_SIMU_TURN = 1

class Troop:
    def __init__(self, t_id, number, eta, owner, is_bomb, link, sender, destination):
        self.t_id = t_id
        self.number = number
        self.eta = eta
        self.owner = owner
        self.is_bomb = is_bomb
        self.link = link
        self.origin = sender
        self.destination = destination


class Path:
    '''
    Class managing alternatives ways to go from an origin to a destination with the same time of travel
    '''

    def __init__(self, origin, intermediate, destination):
        self.origin = origin
        self.destination = destination
        self.intermediate = intermediate
        self.conquest_priority = 0

    def define_conquest_priority(self):
        self.conquest_priority = self.origin.links[self.intermediate.f_id].conquest_priority[self.origin.f_id] + self.intermediate.links[self.destination.f_id].conquest_priority[self.intermediate.f_id]


class Order:
    '''
    Manage orders expressed by the factories
    '''

    MOVE = 0
    INC = 1
    BOMB = 2
    WAIT = 3

    def __init__(self, action, origin, destination, number):
        self.type = action
        self.number = number
        self.origin = origin
        self.destination = destination

    def to_str(self):
        '''
        Translate the order into string
        :return: translated message
        '''
        if self.type == Order.MOVE:
            msg = 'MOVE ' + str(self.origin.f_id) + ' ' + str(self.destination.f_id) + ' ' + str(self.number)
        elif self.type == Order.INC:
            msg = 'INC ' + str(self.origin.f_id)
        elif self.type == Order.BOMB:
            msg = 'BOMB ' + str(self.origin.f_id) + ' ' + str(self.destination.f_id)
        else :
            msg = 'WAIT'

        return msg


class Link:
    def __init__(self, l_id, fact_1, fact_2, distance):
        self.l_id = l_id
        self.distance = distance

        # Troops going towards the factory set as key
        self.troops = {}
        self.troops[fact_1.f_id] = []
        self.troops[fact_2.f_id] = []

        # Other factory at the end of link
        self.destination = {}
        self.destination[fact_1.f_id] = fact_2
        self.destination[fact_2.f_id] = fact_1

    def get_friendly_troops_for_battle(self, factory):
        '''
        Return the number of friendly troops for the factory ready to engage in a battle
        friendly troop = troops with the same owner as the factory
        except for neutral factory, friendly troops are the troop of the player
        :param factory: factory considered
        :return: number of troops
        '''

        if factory.owner != 0:
            match_troops = [troop for troop in self.troops[factory.f_id] if troop.eta == 0 and troop.owner == factory.owner]
        else:
            match_troops = [troop for troop in self.troops[factory.f_id] if troop.eta == 0 and troop.owner == FRIEND]

        if len(match_troops) == 0:
            return 0
        else:
            return sum(troop.number for troop in match_troops)

    def get_ennemy_troops_for_battle(self, factory):
        '''
        Return the number of ennemy troops for the factory ready to engage in a battle
        Ennemy troop = troops with a different owner of the factory
        Except for neutral factory, ennemy troops are the troop of the "ennemy"
        :param factory: factory considered
        :return: number of troops
        '''

        if factory.owner != 0:
            match_troops = [troop for troop in self.troops[factory.f_id] if troop.eta == 0 and troop.owner != factory.owner]
        else:
            match_troops = [troop for troop in self.troops[factory.f_id] if troop.eta == 0 and troop.owner == ENNEMY]

        if len(match_troops) == 0:
            return 0
        else:
            return sum(troop.number for troop in match_troops)

    def get_bomb_eta(self, factory):
        '''
        Return the bomb eta for the factory if a bomb is placed on the link
        :param factory: factory considered
        :return: eta of the closest bomb or -1
        '''

        match_troops = [troop for troop in self.troops[factory.f_id] if troop.is_bomb]

        if len(match_troops) != 0:
            match_troops.sort(key=getattr('eta'))
            return match_troops[0]
        else:
            return -1

    def move_troops(self):
        '''
        Move all the troops along the link (reduce ETA of 1)
        Troops with an ETA of 0 are deleted
        '''

        for factory_troops in self.troops.values():
            i = 0
            while i < len(factory_troops):
                if factory_troops[i].eta > 0:
                    factory_troops[i].eta -= 1
                    i += 1
                else:
                    del factory_troops[i]


    def add_troops(self, origin, destination, number, is_bomb, game):
        '''
        Create and add new troops on the link
        :param origin: factory creating the troops
        :param destination: factory destination of the troops
        :param number: number of the troops
        :param is_bomb: the troop is a bomb
        '''

        troop = Troop(game.next_id_troop(), number, self.distance, origin.owner, is_bomb, self, origin, destination)
        self.troops[destination.f_id].append(troop)
        game.troops.append(troop)

class Factory:
    def __init__(self, f_id):
        self.f_id = f_id
        self.stock = 0
        self.production = 0
        self.current_production = 0
        self.links = {}
        self.alternative_pathes = {}
        self.owner = 0

        self.max_distance = 0
        self.min_distance = 20
        self.max_friend_distance = 0
        self.min_friend_distance = 20
        self.max_ennemy_distance = 0
        self.min_ennemy_distance = 20

        self.nb_friendly_troops = 0
        self.nb_ennemy_troops = 0

        self.bomb_eta = -1

        self.count_zero_prod = 0
        self.count_next_increase = 0

        self.priorities = {}
        self.orders = []

    def clone(self):
        clone = Factory(self.f_id)

        # Duplicate the map but keep the reference to the original link (for now)
        for key, link in self.links.items():
            clone.links[key] = link

        # Duplicate the map and duplicate the array for each key but keep the reference to the original path (for now)
        for key, path in self.alternative_pathes.items():
            clone.alternative_pathes[key] = []

            for path in self.alternative_pathes[key]:
                clone.alternative_pathes[key].append(path)

        clone.stock = self.stock
        clone.production = self.production
        clone.current_production = self.current_production
        clone.owner = self.owner
        clone.max_distance = self.max_distance
        clone.min_distance = self.min_distance
        clone.max_friend_distance = self.max_friend_distance
        clone.min_friend_distance = self.min_friend_distance
        clone.max_ennemy_distance = self.max_ennemy_distance
        clone.min_ennemy_distance = self.min_ennemy_distance
        clone.count_zero_prod = self.count_zero_prod
        clone.count_next_increase = self.count_next_increase

        return clone

    def set_owner(self, owner):
        self.owner = owner

    def set_distances(self):
        self.max_distance = 0
        self.min_distance = 20
        for key, link in self.links.items():
            if link.distance > self.max_distance:
                self.max_distance = link.distance

            if link.distance < self.min_distance:
                self.min_distance = link.distance

            fact_destination = link.destination[self.f_id]
            if self.owner == -1:
                if fact_destination.owner == -1:
                    self.set_friend_distances(link.distance)
                elif fact_destination.owner == 1:
                    self.set_ennemy_distances(link.distance)
                    # else - do not need to know the min/max distance of neutral factories
            else:  # neutral factories are taking into account here to detect if an ennemy base is closer
                if fact_destination.owner == -1:
                    self.set_ennemy_distances(link.distance)
                elif fact_destination.owner == 1:
                    self.set_friend_distances(link.distance)
                    # else - do not need to know the min/max distance of neutral factories

    def set_friend_distances(self, distance):
        if distance > self.max_friend_distance:
            self.max_friend_distance = distance

        if distance < self.min_friend_distance:
            self.min_friend_distance = distance

    def set_ennemy_distances(self, distance):
        if distance > self.max_ennemy_distance:
            self.max_ennemy_distance = distance

        if distance < self.min_ennemy_distance:
            self.min_ennemy_distance = distance

    def set_production(self, production, before_activation):
        self.production = production
        if before_activation != 0:
            self.current_production = 0
        else:
            self.current_production = production

        self.count_zero_prod = before_activation

    def sent_troops(self, destination_id, new_troop):
        '''
        The factory sent new troop to another factory
        :param destination_id: destination factory id
        :param new_troop: troop sent
        '''
        self.links[destination_id].troops[destination_id].append(new_troop)

    def set_bomb_eta(self, eta):
        '''
        Manage the bomb arrival on the factory when known
        Effect on the production is managed in the set_production function
        '''
        self.bomb_eta = eta

    def restore_productivity(self):
        if self.count_zero_prod > 0:
            self.count_zero_prod -= 1

        if self.count_next_increase > 0:
            self.count_next_increase -= 1

    def reset_distances(self):
        self.max_friend_distance = 0
        self.min_friend_distance = 20
        self.max_ennemy_distance = 0
        self.min_ennemy_distance = 20

    def reset_orders(self):
        self.orders.clear()

    def decrease_bombs(self):
        if self.bomb_eta >= 0:
            self.bomb_eta -= 1
        else:
            self.bomb_eta = -1

    def is_production_increasing_feasible(self, is_danger_situation):
        '''
        Return true if the factory can increase its production by one
        '''
        return self.count_next_increase == 0 and self.stock >= 10 and not is_danger_situation

    def get_estimated_stock(self, nb_turn_production):
        '''
        Return the estimated stock of the factory after nb_turn_production set in parameter
        Take into account time +1 due to the engine game making the factory produce before the battles
        '''

        estimated_production = self.production * (nb_turn_production + 1)
        return estimated_production + self.stock

    def solve_turn(self, game):
        '''
        Solve the current turn for the factory
        '''
        self.update_troops_after_moves()
        self.emit_orders()
        self.execute_orders(game) #Execute orders = troops leaving the factory are not taken into account for battle
        self.solve_battle() # Solve battles (a production takes place before battle)
        self.manage_bomb()

    def solve_battle(self):
        '''
        Solve the battle for the factory
        (a production takes place before battle)
        '''
        if self.owner == 1:
            new_stock = self.current_production + self.stock - self.nb_ennemy_troops + self.nb_friendly_troops
        elif self.owner == -1:
            new_stock = self.current_production + self.stock - self.nb_friendly_troops + self.nb_ennemy_troops
        else:
            new_stock = self.stock - self.nb_friendly_troops - self.nb_ennemy_troops

        owner = self.owner
        if owner == 1 and new_stock < 0:
            owner = -1
        elif owner == -1 and new_stock < 0:
            owner = 1
        elif owner == 0 and new_stock < 0:
            if self.nb_friendly_troops > self.nb_ennemy_troops:
                owner = 1
            else:
                owner = -1
                # else the factory is still neutral

        self.owner = owner

        # stock is always positive (negative is positive for new owner)
        self.stock = abs(new_stock)

    def manage_bomb(self):
        '''
        Manage the bomb explosion
        '''
        if self.bomb_eta == 0:
            self.count_zero_prod = 5
            if self.stock >= 20:
                self.stock = round(self.stock / 2)
            else:
                self.stock = max(self.stock - 10, 0)

        if self.count_zero_prod > 0:
            self.current_production = 0
        else:
            self.current_production = self.production

        if self.count_zero_prod >= 0:
            self.count_zero_prod -= 1

    def compute_troops_to_send(self, fact_destination):
        '''
        Compute the number of troops to send to conquer the objective on next ruen as if the distance was one turn
        '''

        if self.owner == fact_destination.owner :
            nb_cyborg_friends = fact_destination.nb_friendly_troops
            nb_cyborg_ennemies = fact_destination.nb_ennemy_troops
        elif fact_destination.owner == 0:
            nb_cyborg_friends = fact_destination.nb_friendly_troops
            nb_cyborg_ennemies = fact_destination.nb_ennemy_troops
        else:
            nb_cyborg_friends = fact_destination.nb_ennemy_troops
            nb_cyborg_ennemies = fact_destination.nb_friendly_troops

        link = self.links[fact_destination.f_id]

        if fact_destination.count_zero_prod > 0:
            estimated_stock = fact_destination.stock
        else:
            estimated_stock = fact_destination.get_estimated_stock(0)

        if fact_destination.owner == 0:
            send_troops = fact_destination.stock + DELTA_CONQUER - nb_cyborg_friends + nb_cyborg_ennemies
        elif fact_destination.owner == -1:
            send_troops = estimated_stock + DELTA_CONQUER + nb_cyborg_ennemies - nb_cyborg_friends
        else: #owner == 1
            if fact_destination.production == 3:
                send_troops = nb_cyborg_ennemies - nb_cyborg_friends - estimated_stock
            else:
                send_troops = fact_destination.stock + NB_CYBORG_INC - nb_cyborg_friends + nb_cyborg_ennemies

        send_troops = max(send_troops, 0)  # no negative number

        return send_troops

    def is_bomb_sendable(self, link, fact_destination):
        #TODO : game or factory ???
        return False

    def emit_orders(self, simu = None):
        '''
        Define the orders emitted by owned factory
        '''

        self.define_conquest_priorities(simu)
        factory_stock = self.stock
        factory_production = self.production

        delta_agression = self.nb_ennemy_troops - self.nb_friendly_troops
        is_danger_situation = delta_agression > (factory_stock - 10) or (self.owner == -1) or (self.count_zero_prod > 0)

        if self.f_id == 0:
            print('danger situation = ' + str(is_danger_situation) + ', delta_agression = ' + str(delta_agression) + ', zero prod = ' + str(self.count_zero_prod), file=sys.stderr)

        if (self.is_production_increasing_feasible(is_danger_situation)):
            factory_stock -= 10
            factory_production += 1
            self.orders.append(Order(Order.INC, self, None, 10))

        if self.bomb_eta == 1:
            keep_troops = 0
        else:
            keep_troops = max(delta_agression, 0)

        sendable_troops = max(factory_stock - keep_troops, 0)

        sorted_links = sorted(self.links.values(), key=lambda link: link.distance)
        while len(sorted_links) > MIN_FACTORY_CONSIDERED and sorted_links[len(sorted_links) - 1].distance >= MAX_DISTANCE_CONSIDERED:
            sorted_links.pop()

        sorted_priorities= [(k, self.priorities[k]) for k in sorted(self.priorities, key=lambda priority: priority, reverse=True)]

        for prio_factory_id, priority in sorted_priorities:
            link = self.links[prio_factory_id]
            fact_destination = link.destination[self.f_id]
            print('target : ' + str(fact_destination.f_id) + ' - priority ' + str(priority) + ' - distance ' + str(link.distance), file=sys.stderr)

            #alternative_pathes = sorted(self.alternative_pathes[fact_destination.f_id], key=lambda path: (-path.intermediate.owner, -path.conquest_priority))

            #for path in alternative_pathes:
            #    print('alt : ' + str(path.intermediate.f_id), file=sys.stderr)

            #if len(alternative_pathes) != 0:
            #    alternative_path = alternative_pathes[0]
            #else:
            #    alternative_path = None

            if self.is_bomb_sendable(link, fact_destination):
                self.orders.append(Order(Order.BOMB, self, fact_destination, 0))
                fact_destination.set_bomb_eta(link.distance)
            else:

                send_troops = self.compute_troops_to_send(fact_destination)
                destination_id = fact_destination.f_id
                destination = fact_destination

                print('send troops : ' + str(send_troops) + ', sendable troops : ' + str(sendable_troops), file=sys.stderr)

                #if alternative_path is not None and send_troops < sendable_troops:
                #    print('alternative path fact : ' + str(path.intermediate.f_id), file=sys.stderr)

                #    intermediate_troop = self.compute_troops_to_send(path.intermediate)
                #    send_troops += intermediate_troop
                #    destination_id = path.intermediate.f_id
                #    destination = path.intermediate

                #    print('new troops = ' + str(send_troops), file=sys.stderr)

                send_troops = min(send_troops, sendable_troops)
                if send_troops != 0:
                    # if send_troops <= sendable_troops:

                    self.orders.append(Order(Order.MOVE, self, destination, send_troops))

                    factory_stock -= send_troops
                    sendable_troops -= send_troops

                    if sendable_troops == 0:
                        break

        if len(self.orders) == 0:
            self.orders.append(Order(Order.WAIT, self, None, 0))

    def build_path(self):
        '''
        Build alternative path of the same time from the factory to reach the other factories
        '''

        for key, destination_link in self.links.items():
            self.alternative_pathes[destination_link.destination[self.f_id].f_id] = self.build_pathes_for_destination(destination_link)

    def build_pathes_for_destination(self, destination_link):
        '''
        List all the intermediates from where the troops can go to destination without delay
        @param destination_link: link connecting directly to the destination from the origin
        '''

        pathes = []
        destination = destination_link.destination[self.f_id]
        links_to_visit = sorted(self.links.values(), key=lambda link: (link.distance))

        for link in links_to_visit:
            if link.distance >= destination_link.distance - 2:
                # Distance already too big to fit, and other will be too big as well
                break
            else:
                intermediate = link.destination[self.f_id]
                second_link = intermediate.links[destination.f_id]
                if second_link.distance >= (destination_link.distance - link.distance - 1):
                    # Distance already too big to fit, and other will be too big as well
                    break
                else:
                    pathes.append(Path(self, intermediate, destination))

        return pathes

    def define_conquest_priorities(self, simu=None):
        '''
        Update the priorities for each destination
        '''

        for key, link in self.links.items():
            if simu is None:
                destination = link.destination[self.f_id]
            else:
                destination = simu.factories[link.destination[self.f_id].f_id]

            self.priorities[key] = self.define_conquest_priority(destination)

    def define_conquest_priority(self, factory_destination):
        '''
        Compute the priority for the factory set as origin
        to conquer the factory at the other side of the link
        Priority goes as :
        - The factory is not owned > ennemy > owned
        - Higher factory production is the better
        - Closer the factory is the better
        @param origin : factory from where the cyborgs are emitted from
        '''

        link = factory_destination.links[self.f_id]
        estimated_distance = min(link.distance + 1, 20)

        nb_cyborg_ennemies = self.nb_ennemy_troops #sum(factory_destination.cyborgs_coming[ENNEMY][estimated_distance:NB_PREDICTED_TURN])
        nb_cyborg_friends = self.nb_friendly_troops #sum(factory_destination.cyborgs_coming[FRIEND][estimated_distance:NB_PREDICTED_TURN])

        estimated_stock = factory_destination.get_estimated_stock(self.links[factory_destination.f_id].distance - factory_destination.count_zero_prod)

        if factory_destination.owner == 1 and nb_cyborg_ennemies > (estimated_stock + nb_cyborg_friends):  # and self.distance < (origin.min_friend_distance + FIRST_EXPLORATION_DELTA)
            # R2 : help your neighbor
            priority = 10 * 1000
            priority += (20 - link.distance) * 10
            priority += factory_destination.production
            priority += nb_cyborg_ennemies

        elif factory_destination.owner == 0 and factory_destination.min_friend_distance < factory_destination.min_ennemy_distance:  # and factory_destination.production > 0
            # R1 : expand around you on factories of interest
            priority = 9 * 1000
            # priority += factory_destination.production * 100
            # priority -= (origin.stock - factory_destination.stock) #Smaller the difference of stock, best it is
            priority += factory_destination.production * 10
            priority += len(self.alternative_pathes[factory_destination.f_id]) * 100
            priority += 20 - link.distance

        elif factory_destination.owner == 1 and factory_destination.production <= 1 and estimated_stock <= 10:
            # R3 : increase the capacity of your neighbor
            priority = 8 * 1000
            priority += (20 - link.distance) * 10
            priority += 3 - factory_destination.production

        elif factory_destination.owner == -1 and ((factory_destination.bomb_eta != 0 and link.distance == (factory_destination.bomb_eta + 1)) or (factory_destination.count_zero_prod - 1 == link.distance )):
            # R4 : attack your close opponent where he is bombed
            priority = 7 * 1000
            priority += (20 - factory_destination.bomb_eta * 10)
            priority += (5 - factory_destination.count_zero_prod * 10)
            priority += factory_destination.production
        elif factory_destination.owner == -1 and (estimated_stock + nb_cyborg_friends - nb_cyborg_ennemies) < 20 and link.distance < (self.min_ennemy_distance + FIRST_EXPLORATION_DELTA) and factory_destination.current_production >= 1:
            # R5 : attack your close opponent where he is weak
            priority = 6 * 1000
            # priority += (20 - link.distance ) * 100
            # priority += (3-factory_destination.current_production) * 10 - factory_destination.stock
            priority -= estimated_stock + nb_cyborg_friends
            priority += nb_cyborg_ennemies

        elif factory_destination.owner == 0 and factory_destination.production > 0:
            # R6 : expand
            priority = 5 * 1000
            priority += factory_destination.production * 10 - factory_destination.stock
            priority += 20 - link.distance
        elif factory_destination.owner == -1 and nb_cyborg_friends < 20:
            # R7 : attack your ennemy where is weak
            priority = 4 * 1000
            priority += (20 - link.distance ) * 10
        elif factory_destination == 1:
            # R8 :defense
            priority = 3 * 1000
            priority += 100 - factory_destination.stock
        elif factory_destination.owner == 0:
            priority = 2 * 1000
        else:
            # R9 :attack
            priority = 1 * 1000
            priority += (20 - link.distance ) * 10
            priority += (3 - factory_destination.current_production)

        return priority

    def generate_message_orders(self):
        '''
        Generate orders as string to send to game engine
        :return: message
        '''

        msg = ''
        for order in self.orders:
            msg += order.to_str()
            msg += ';'

        return msg

    def update_troops_after_moves(self):
        '''
        update the number of friendly/ennemy troops engaged in battle at the factory
        '''

        self.nb_friendly_troops = 0
        self.nb_ennemy_troops = 0

        for link in self.links.values():
            self.nb_friendly_troops += link.get_friendly_troops_for_battle(self)
            self.nb_ennemy_troops += link.get_ennemy_troops_for_battle(self)
            self.bomb_eta = link.get_bomb_eta(self)

    def execute_orders(self, game):
        '''
        Execute the orders for the factory
        '''

        move_orders = [order for order in self.orders if order.type == Order.MOVE or order.type == Order.INC]
        for order in move_orders:
            self.stock -= order.number
            if order.type == Order.INC:
                self.production += 1
                self.count_next_increase = COUNT_INCREASE
                if self.count_zero_prod <= 0:
                    self.current_production = self.production

            elif order.type == Order.MOVE:  #Move order
                self.links[order.destination.f_id].add_troops(self, order.destination, order.number, False,game)
            else: #Bomb order
                self.links[order.destination.f_id].add_troops(self, order.destination, 0, True,game)

        self.orders.clear()


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

factory_count = int(input())  # the number of factories
link_count = int(input())  # the number of links between factories

game = Game()
simu = Game()

game.initialize_game(factory_count, link_count)
simu.initialize_game(factory_count, link_count)

game.create_factories()
simu.create_factories()

for i in range(link_count):
    factory_1, factory_2, distance = [int(j) for j in input().split()]
    game.add_link(factory_1, factory_2, distance)
    simu.add_link(factory_1, factory_2, distance)

game.initialize_factories()
simu.initialize_factories()

# game loop
while True:
    game.reset()
    simu.reset()

    entity_count = int(input())  # the number of entities (e.g. factories and troops)
    for i in range(entity_count):
        entity_id, entity_type, arg_1, arg_2, arg_3, arg_4, arg_5 = input().split()
        entity_id = int(entity_id)
        arg_1 = int(arg_1)
        arg_2 = int(arg_2)
        arg_3 = int(arg_3)
        arg_4 = int(arg_4)
        arg_5 = int(arg_5)

        game.process_input(entity_id, entity_type, arg_1, arg_2, arg_3, arg_4, arg_5)
        simu.process_input(entity_id, entity_type, arg_1, arg_2, arg_3, arg_4, arg_5)

    game.consolidate_inputs()
    simu.consolidate_inputs()

    for i in range(NB_SIMU_TURN):
        simu.simulate_turn()

    game.solve_turn(simu)