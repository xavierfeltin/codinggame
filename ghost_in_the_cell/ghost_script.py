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

        self.cyborgs_coming = {}
        self.cyborgs_coming[FRIEND] = []
        self.cyborgs_coming[ENNEMY] = []
        self.bomb_eta = -1

        self.count_zero_prod = 0
        self.count_next_increase = 0

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

        # Duplicate the map and duplicate the array for each key but keep the reference to the original coming cyborgs (for now)
        for key, cyborg in self.cyborgs_coming.items():
            clone.cyborgs_coming[key] = []

            for cyborg in self.cyborgs_coming[key]:
                clone.cyborgs_coming[key].append(cyborg)

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

        if (self.owner == -1 or self.owner == 1) and self.owner != owner:
            self.cyborgs_coming[NEUTRAL] = self.cyborgs_coming.pop(ENNEMY)
            self.cyborgs_coming[NEUTRAL_2] = self.cyborgs_coming.pop(FRIEND)
            self.cyborgs_coming[FRIEND] = self.cyborgs_coming.pop(NEUTRAL)
            self.cyborgs_coming[ENNEMY] = self.cyborgs_coming.pop(NEUTRAL_2)

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
        if turn == 1:
            self.production = production
            self.current_production = production
        else:
            if before_activation != 0:
                self.current_production = 0
            else:
                self.current_production = production

        self.count_zero_prod = before_activation

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

    def initialize_nb_cyborgs_coming(self):
        '''
        Initialize the size of cyborgs coming function of the maximum distance between factories
        '''
        for i in range(self.max_distance):
            self.cyborgs_coming[FRIEND].append(0)
            self.cyborgs_coming[ENNEMY].append(0)

    def reset_cyborgs(self):
        for i in range(self.max_distance):
            self.cyborgs_coming[FRIEND][i] = 0
            self.cyborgs_coming[ENNEMY][i] = 0

    def reset_distances(self):
        self.max_friend_distance = 0
        self.min_friend_distance = 20
        self.max_ennemy_distance = 0
        self.min_ennemy_distance = 20

    def decrease_bombs(self):
        if self.bomb_eta >= 0:
            self.bomb_eta -= 1
        else:
            self.bomb_eta = -1

    def is_bomb_sendable(self, link, fact_destination):
        '''
        Return true if a bomb can be sent by the factory
        '''

        # nb_cyborg_player = sum(fact_destination.cyborgs_coming[ENNEMY][0:link.distance])
        # nb_cyborg_ennemy = sum(fact_destination.cyborgs_coming[FRIEND][0:link.distance])

        nb_cyborg_player = sum(fact_destination.cyborgs_coming[ENNEMY][0:NB_PREDICTED_TURN_BOMB])
        nb_cyborg_ennemy = sum(fact_destination.cyborgs_coming[FRIEND][0:NB_PREDICTED_TURN_BOMB])

        estimated_stock = fact_destination.get_estimated_stock(NB_PREDICTED_TURN_BOMB - self.count_zero_prod)

        evaluated_defense = nb_cyborg_ennemy + estimated_stock
        nb_defense_left = evaluated_defense - nb_cyborg_player

        return fact_destination.owner == -1 and link.distance <= MAX_BOMB_DISTANCE and nb_defense_left >= MIN_DEFENSE_TO_SEND_BOMB and (fact_destination.current_production >= 2 \
                                                                                                                                        or len(factories_ennemy) == 1) and fact_destination.bomb_eta == -1 and available_bomb != 0

    def is_production_increasing_feasible(self, is_danger_situation):
        '''
        Return true if the factory can increase its production by one
        '''
        return (not (len(factories_owned) == 1)) and self.count_next_increase == 0 and self.stock >= 10 and not is_danger_situation

    def get_estimated_stock(self, nb_turn_production):
        '''
        Return the estimated stock of the factory after nb_turn_production set in parameter
        Take into account time +1 due to the engine game making the factory produce before the battles
        '''

        estimated_production = self.production * (nb_turn_production + 1)
        return estimated_production + self.stock

    def solver(self, fact_destination):
        '''
        Compute the state of the destination factory function of the distance with a maximum simulation time
        @param fact_destination : factory targeted
        @return a clone of the factory updated by the solver
        '''

        clone_dest = fact_destination.clone()

        if fact_destination.f_id == self.f_id:
            # Predict its own state in the future
            time = NB_PREDICTED_TURN
        else:
            # Predict the future of the target function of the distance between them
            time = min(self.links[fact_destination.f_id].distance, NB_PREDICTED_TURN)

        i = 0
        while i <= time:

            # Move troops and bombs
            # move troops is simulated by using the first index of the cyborg_coming list
            if clone_dest.bomb_eta >= 0:
                clone_dest.bomb_eta -= 1

            # Solve battles (a production takes place before battle)
            if clone_dest.owner == 1:
                new_stock = clone_dest.current_production + clone_dest.stock - clone_dest.cyborgs_coming[ENNEMY][0] + clone_dest.cyborgs_coming[FRIEND][0]
            elif fact_destination.owner == -1:
                new_stock = clone_dest.current_production + clone_dest.stock - clone_dest.cyborgs_coming[FRIEND][0] + clone_dest.cyborgs_coming[ENNEMY][0]
            else:
                new_stock = clone_dest.stock - clone_dest.cyborgs_coming[FRIEND][0] - clone_dest.cyborgs_coming[ENNEMY][0]

            owner = clone_dest.owner
            if owner == 1 and new_stock < 0:
                owner = -1
            elif owner == -1 and new_stock < 0:
                owner = 1
            elif owner == 0 and new_stock < 0:
                if clone_dest.cyborgs_coming[FRIEND][0] > clone_dest.cyborgs_coming[ENNEMY][0]:
                    owner = 1
                else:
                    owner = -1
                    # else the factory is still neutral

            # Manage bomb explosion
            if clone_dest.bomb_eta == 0:
                clone_dest.count_zero_prod = 5

            if clone_dest.count_zero_prod > 0:
                clone_dest.current_production = 0
            else:
                clone_dest.current_production = clone_dest.production

            if clone_dest.count_zero_prod >= 0:
                clone_dest.count_zero_prod -= 1

            # Update the destination factory
            clone_dest.owner = owner
            clone_dest.stock = new_stock

            # Produce new units for the factories close enough during the simulation turn
            sorted_links = sorted(clone_dest.links.values(), key=lambda link: link.distance)

            j = 0
            distance = sorted_links[j].distance
            while (distance <= time) and j < len(sorted_links):

                # origin = sorted_links[connected_factories_id[j]].destination[clone_dest.f_id]
                origin = sorted_links[j].destination[clone_dest.f_id]
                if origin.owner != 0:
                    nb_sent_troops = origin.production

                    if clone_dest.owner == origin.owner or (clone_dest.owner == 0 and origin.owner == 1):
                        clone_dest.cyborgs_coming[FRIEND][distance] += nb_sent_troops
                    elif clone_dest.owner != origin.owner:
                        clone_dest.cyborgs_coming[ENNEMY][distance] += nb_sent_troops

                j += 1
                if j < len(sorted_links):
                    distance = sorted_links[j].distance

            if len(clone_dest.cyborgs_coming[ENNEMY]) > 0:
                # clone_dest.cyborgs_coming[ENNEMY].pop(0) #replace pop by shift
                clone_dest.cyborgs_coming[ENNEMY] = clone_dest.cyborgs_coming[ENNEMY][1:] + clone_dest.cyborgs_coming[ENNEMY][:1]
                clone_dest.cyborgs_coming[ENNEMY][len(clone_dest.cyborgs_coming[ENNEMY]) - 1] = 0

            if len(clone_dest.cyborgs_coming[FRIEND]) > 0:
                # clone_dest.cyborgs_coming[FRIEND].pop(0) #replace pop by shift
                clone_dest.cyborgs_coming[FRIEND] = clone_dest.cyborgs_coming[FRIEND][1:] + clone_dest.cyborgs_coming[FRIEND][:1]
                clone_dest.cyborgs_coming[FRIEND][len(clone_dest.cyborgs_coming[FRIEND]) - 1] = 0

            i += 1

        # TODO:
        # Define the clone function of a factory => ok
        # Push the troop on the factory forward instad of using i each time => ok
        # Manage the production if there is a bomb coming !!! => ok
        # Add prediction of production of neighbor factories => on going
        # Use the clone to estimate the number of troops to send (see if useful for link priority as well)

        return clone_dest

    def compute_troops_to_send(self, fact_destination):
        '''
        Compute the number of troops to send to conquer the objective
        '''

        # TODO : add a "solver" to simulate the state of the destination factory when the troops will arrive
        # function of the cyborgs already going to the factory, plus new cyborgs coming from the factories closer than self
        # euristic : nb new cyborgs = factory production

        simulated_factory = self.solver(fact_destination)

        nb_cyborg_friends = fact_destination.cyborgs_coming[FRIEND][NB_PREDICTED_TURN]
        nb_cyborg_ennemies = fact_destination.cyborgs_coming[ENNEMY][NB_PREDICTED_TURN]

        if simulated_factory.owner == 0:
            if simulated_factory.production > 0:
                send_troops = simulated_factory.stock + DELTA_CONQUER - nb_cyborg_friends + nb_cyborg_ennemies
            else:
                send_troops = simulated_factory.stock + NB_CYBORG_INC - nb_cyborg_friends + nb_cyborg_ennemies
        elif simulated_factory.owner == -1:
            send_troops = simulated_factory.stock + DELTA_CONQUER + nb_cyborg_ennemies - nb_cyborg_friends
        else:  # owner == 1
            if simulated_factory.production == 3:
                send_troops = nb_cyborg_ennemies - nb_cyborg_friends - simulated_factory.stock
            else:
                send_troops = simulated_factory.stock + NB_CYBORG_INC - nb_cyborg_friends + nb_cyborg_ennemies

        '''
        #nb_cyborg_friends = sum(fact_destination.cyborgs_coming[FRIEND][0:link.distance])
        #nb_cyborg_ennemies = sum(fact_destination.cyborgs_coming[ENNEMY][0:link.distance])

        nb_cyborg_friends = sum(fact_destination.cyborgs_coming[FRIEND][0:NB_PREDICTED_TURN])
        nb_cyborg_ennemies = sum(fact_destination.cyborgs_coming[ENNEMY][0:NB_PREDICTED_TURN])

        if fact_destination.bomb_eta < link.distance and fact_destination.bomb_eta != -1  :
            estimated_stock = fact_destination.get_estimated_stock(fact_destination.bomb_eta + (link.distance - 5))
        else:
            estimated_stock = fact_destination.get_estimated_stock(link.distance - fact_destination.count_zero_prod)

        if fact_destination.owner == 0:
            if fact_destination.production > 0 :
                send_troops = fact_destination.stock + DELTA_CONQUER - nb_cyborg_friends + nb_cyborg_ennemies
            else:
                send_troops = fact_destination.stock + NB_CYBORG_INC - nb_cyborg_friends + nb_cyborg_ennemies
        elif fact_destination.owner == -1:
            send_troops = estimated_stock + DELTA_CONQUER + nb_cyborg_ennemies - nb_cyborg_friends
        else: #owner == 1
            if fact_destination.production == 3:
                send_troops = nb_cyborg_ennemies - nb_cyborg_friends - estimated_stock
            else:
                send_troops = fact_destination.stock + NB_CYBORG_INC - nb_cyborg_friends + nb_cyborg_ennemies
        '''

        send_troops = max(send_troops, 0)  # no negative number

        return send_troops

    def emit_orders(self):
        '''
        Define the orders emitted by owned factory
        '''

        message = ''
        message_bomb = ''
        message_increase = ''

        '''
        delta_agression = sum(self.cyborgs_coming[ENNEMY][0:NB_PREDICTED_TURN]) - sum(self.cyborgs_coming[FRIEND][0:NB_PREDICTED_TURN])
        is_danger_situation = delta_agression > (self.stock - 10)

        if self.f_id == 0:
            print('danger situation = ' + str(is_danger_situation) + ', delta_agression = ' + str(delta_agression), file=sys.stderr)

        if (self.is_production_increasing_feasible(is_danger_situation)):
            self.stock -= 10
            self.production += 1
            self.count_next_increase = COUNT_INCREASE
            message_increase = 'INC ' + str(self.f_id)

        if self.bomb_eta == 1 :
            keep_troops = 0
        else:
            keep_troops = max(delta_agression, 0)

        if self.current_production == 0:
            if len(factories_owned) == 1:
                sendable_troops = max(self.stock - keep_troops, 0)
            else:
                sendable_troops = 0
        else:
            sendable_troops = max(self.stock - keep_troops, 0)
        '''

        simulated_factory = self.solver(self)

        delta_agression = simulated_factory.cyborgs_coming[ENNEMY][0] - simulated_factory.cyborgs_coming[FRIEND][0]
        is_danger_situation = delta_agression > (simulated_factory.stock - 10) or (simulated_factory.owner == -1) or (simulated_factory.count_zero_prod > 0)

        if simulated_factory.f_id == 0:
            print('danger situation = ' + str(is_danger_situation) + ', delta_agression = ' + str(delta_agression) + ', zero prod = ' + str(simulated_factory.count_zero_prod), file=sys.stderr)

        if (simulated_factory.is_production_increasing_feasible(is_danger_situation)):
            simulated_factory.stock -= 10
            simulated_factory.production += 1
            simulated_factory.count_next_increase = COUNT_INCREASE
            message_increase = 'INC ' + str(simulated_factory.f_id)

        if simulated_factory.bomb_eta == 1:
            keep_troops = 0
        else:
            keep_troops = max(delta_agression, 0)

        if self.current_production == 0:
            if len(factories_owned) == 1:
                sendable_troops = max(self.stock - keep_troops, 0)
            else:
                sendable_troops = 0
        else:
            sendable_troops = max(self.stock - keep_troops, 0)

        print('factory : ' + str(self.f_id), file=sys.stderr)

        sorted_links = sorted(self.links.values(), key=lambda link: link.distance)
        while len(sorted_links) > MIN_FACTORY_CONSIDERED and sorted_links[len(sorted_links) - 1].distance >= MAX_DISTANCE_CONSIDERED:
            sorted_links.pop()

        # sorted_links = sorted(self.links.values(), key=lambda link: link.conquest_priority[self.f_id], reverse=True)
        sorted_links = sorted(sorted_links, key=lambda link: link.conquest_priority[self.f_id], reverse=True)

        for link in sorted_links:
            fact_destination = link.destination[self.f_id]
            print('target : ' + str(fact_destination.f_id) + ' - priority ' + str(link.conquest_priority[self.f_id]) + ' - distance ' + str(link.distance), file=sys.stderr)

            alternative_pathes = sorted(self.alternative_pathes[fact_destination.f_id], key=lambda path: (-path.intermediate.owner, -path.conquest_priority))

            for path in alternative_pathes:
                print('alt : ' + str(path.intermediate.f_id), file=sys.stderr)

            if len(alternative_pathes) != 0:  # and alternative_pathes[0].intermediate.owner != -1:
                alternative_path = alternative_pathes[0]
            else:
                alternative_path = None

            if self.is_bomb_sendable(link, fact_destination):
                message_bomb = 'BOMB ' + str(self.f_id) + ' ' + str(fact_destination.f_id)
                send_troops = 0
                fact_destination.set_bomb_eta(link.distance)
            else:

                send_troops = self.compute_troops_to_send(fact_destination)
                destination_id = fact_destination.f_id

                print('send troops : ' + str(send_troops) + ', sendable troops : ' + str(sendable_troops), file=sys.stderr)

                if alternative_path is not None and send_troops < sendable_troops:
                    print('alternative path fact : ' + str(path.intermediate.f_id), file=sys.stderr)

                    intermediate_troop = self.compute_troops_to_send(path.intermediate)
                    send_troops += intermediate_troop
                    destination_id = path.intermediate.f_id

                    print('new troops = ' + str(send_troops), file=sys.stderr)

                send_troops = min(send_troops, sendable_troops)
                if send_troops != 0:
                    # if send_troops <= sendable_troops:
                    if message != '':
                        message += ';'
                    message += 'MOVE ' + str(factory.f_id) + ' ' + str(destination_id) + ' ' + str(send_troops)

                    self.stock -= send_troops
                    sendable_troops -= send_troops

                    if sendable_troops == 0:
                        break

        message_orders = ''
        if message_bomb != '':
            message_orders += message_bomb

        if message != '':
            if message_orders != '':
                message_orders += ';'
            message_orders += message

        if message_increase != '':
            if message_orders != '':
                message_orders += ';'
            message_orders += message_increase

        return message_orders

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


class Troop:
    def __init__(self, t_id, number, eta, owner, is_bomb, link):
        self.t_id = t_id
        self.number = number
        self.eta = eta
        self.owner = owner
        self.is_bomb = is_bomb
        self.link = link


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

        # Priority to conquest the factory set as key
        self.conquest_priority = {}
        self.conquest_priority[fact_1.f_id] = 0  # self.define_conquest_priority(fact_1)
        self.conquest_priority[fact_2.f_id] = 0  # self.define_conquest_priority(fact_2)

    def define_conquest_priorities(self):
        '''
        Update the priorities for each factory on the link
        '''

        for key in self.conquest_priority.keys():
            fact_origin = factories[key]
            self.conquest_priority[key] = self.define_conquest_priority(fact_origin)

    def define_conquest_priority(self, origin):
        '''
        Compute the priority for the factory set as origin
        to conquer the factory at the other side of the link
        Priority goes as :
        - The factory is not owned > ennemy > owned
        - Higher factory production is the better
        - Closer the factory is the better
        @param origin : factory from where the cyborgs are emitted from
        '''

        factory_destination = self.destination[origin.f_id]

        sim_dest = origin.solver(factory_destination)
        sim_origin = origin.solver(origin)

        estimated_distance = min(self.distance + 1, 20)
        nb_cyborg_ennemies = factory_destination.cyborgs_coming[ENNEMY][0]
        nb_cyborg_friends = factory_destination.cyborgs_coming[FRIEND][0]

        estimated_stock = sim_dest.stock

        if sim_dest.owner == 1 and nb_cyborg_ennemies > (estimated_stock + nb_cyborg_friends):  # and self.distance < (origin.min_friend_distance + FIRST_EXPLORATION_DELTA)
            # R2 : help your neighbor
            priority = 10 * 1000
            priority += (20 - self.distance) * 10
            priority += sim_dest.production
            priority += nb_cyborg_ennemies

        elif sim_dest.owner == 0 and sim_dest.min_friend_distance < sim_dest.min_ennemy_distance:  # and factory_destination.production > 0
            # R1 : expand around you on factories of interest
            priority = 9 * 1000
            # priority += factory_destination.production * 100
            # priority -= (origin.stock - factory_destination.stock) #Smaller the difference of stock, best it is
            priority += sim_dest.production * 10
            priority += len(sim_origin.alternative_pathes[factory_destination.f_id]) * 100
            priority += 20 - self.distance

        elif factory_destination.owner == 1 and sim_dest.production <= 1 and estimated_stock <= 10:
            # R3 : increase the capacity of your neighbor
            priority = 8 * 1000
            priority += (20 - self.distance) * 10
            priority += 3 - sim_dest.production

        elif sim_dest.owner == -1 and ((sim_dest.bomb_eta != 0 and self.distance == (sim_dest.bomb_eta + 1)) or (sim_dest.count_zero_prod - 1 == self.distance)):
            # R4 : attack your close opponent where he is bombed
            priority = 7 * 1000
            priority += (20 - sim_dest.bomb_eta * 10)
            priority += (5 - sim_dest.count_zero_prod * 10)
            priority += sim_dest.production
        elif sim_dest.owner == -1 and (estimated_stock + nb_cyborg_friends - nb_cyborg_ennemies) < 20 and self.distance < (sim_origin.min_ennemy_distance + FIRST_EXPLORATION_DELTA) and factory_destination.current_production >= 1:
            # R5 : attack your close opponent where he is weak
            priority = 6 * 1000
            # priority += (20 - self.distance) * 100
            # priority += (3-factory_destination.current_production) * 10 - factory_destination.stock
            priority -= estimated_stock + nb_cyborg_friends
            priority += nb_cyborg_ennemies

        elif sim_dest.owner == 0 and sim_dest.production > 0:
            # R6 : expand
            priority = 5 * 1000
            priority += sim_dest.production * 10 - sim_dest.stock
            priority += 20 - self.distance
        elif sim_dest.owner == -1 and nb_cyborg_friends < 20:
            # R7 : attack your ennemy where is weak
            priority = 4 * 1000
            priority += (20 - self.distance) * 10
        elif sim_dest == 1:
            # R8 :defense
            priority = 3 * 1000
            priority += 100 - sim_dest.stock
        elif sim_dest.owner == 0:
            priority = 2 * 1000
        else:
            # R9 :attack
            priority = 1 * 1000
            priority += (20 - self.distance) * 10
            priority += (3 - sim_dest.current_production)

        '''
        estimated_distance = min(self.distance+1, 20)

        #nb_cyborg_ennemies = sum(factory_destination.cyborgs_coming[ENNEMY][0:self.distance])
        #nb_cyborg_friends = sum(factory_destination.cyborgs_coming[FRIEND][0:self.distance])

        nb_cyborg_ennemies = sum(factory_destination.cyborgs_coming[ENNEMY][estimated_distance:NB_PREDICTED_TURN])
        nb_cyborg_friends = sum(factory_destination.cyborgs_coming[FRIEND][estimated_distance:NB_PREDICTED_TURN])

        estimated_stock = factory_destination.get_estimated_stock(self.distance - factory_destination.count_zero_prod)

        if factory_destination.owner == 1 and nb_cyborg_ennemies  > (estimated_stock + nb_cyborg_friends) : #and self.distance < (origin.min_friend_distance + FIRST_EXPLORATION_DELTA)
            #R2 : help your neighbor
            priority = 10 * 1000
            priority += (20 - self.distance) * 10
            priority += factory_destination.production
            priority += nb_cyborg_ennemies

        elif factory_destination.owner == 0 and factory_destination.min_friend_distance < factory_destination.min_ennemy_distance : #and factory_destination.production > 0
            #R1 : expand around you on factories of interest
            priority = 9 * 1000
            #priority += factory_destination.production * 100
            #priority -= (origin.stock - factory_destination.stock) #Smaller the difference of stock, best it is
            priority += factory_destination.production * 10
            priority += len(origin.alternative_pathes[factory_destination.f_id]) * 100
            priority += 20 - self.distance

        elif factory_destination.owner == 1  and factory_destination.production <= 1 and estimated_stock <= 10:
            #R3 : increase the capacity of your neighbor
            priority = 8 * 1000
            priority += (20 - self.distance) * 10
            priority += 3 - factory_destination.production

        elif factory_destination.owner == -1 and ((factory_destination.bomb_eta != 0 and self.distance == (factory_destination.bomb_eta+1)) or (factory_destination.count_zero_prod-1 == self.distance)) :
            #R4 : attack your close opponent where he is bombed
            priority = 7 * 1000
            priority += (20-factory_destination.bomb_eta * 10)
            priority += (5-factory_destination.count_zero_prod * 10)
            priority += factory_destination.production
        elif factory_destination.owner == -1 and (estimated_stock + nb_cyborg_friends - nb_cyborg_ennemies)  < 20 and self.distance < (origin.min_ennemy_distance + FIRST_EXPLORATION_DELTA) and factory_destination.current_production >= 1 :
            #R5 : attack your close opponent where he is weak
            priority = 6 * 1000
            #priority += (20 - self.distance) * 100
            #priority += (3-factory_destination.current_production) * 10 - factory_destination.stock
            priority -= estimated_stock + nb_cyborg_friends
            priority += nb_cyborg_ennemies

        elif factory_destination.owner == 0 and factory_destination.production > 0 :
            #R6 : expand
            priority = 5 * 1000
            priority += factory_destination.production * 10 - factory_destination.stock
            priority += 20 - self.distance
        elif factory_destination.owner == -1 and nb_cyborg_friends < 20:
            #R7 : attack your ennemy where is weak
            priority = 4 * 1000
            priority += (20 - self.distance) * 10
        elif factory_destination == 1:
            #R8 :defense
            priority = 3 * 1000
            priority += 100 - factory_destination.stock
        elif factory_destination.owner == 0 :
            priority = 2 * 1000
        else:
            #R9 :attack
            priority = 1 * 1000
            priority += (20 - self.distance) * 10
            priority += (3-factory_destination.current_production)
        '''

        return priority


def estimate_target(origin):
    '''
    Choose the possible target of the ennemy bomb and set the bomb eta accordingly
    '''

    if turn == 1:
        target = factories_owned[0]
        eta = origin.links[target.f_id].distance - 1
    else:
        temp = sorted(factories_owned, key=lambda factory: (-factory.bomb_eta, -factory.production, -factory.stock, origin.links[factory.f_id].distance))
        target = temp[0]
        eta = origin.links[target.f_id].distance - 1

    target.set_bomb_eta(eta)
    return target


def check_ennemy_bombs():
    '''
    Update the ennemy bombs on their potential target
    '''
    for target in ennemy_bombs:
        if target is not None and target.bomb_eta == -1:
            target = None


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