import sys
import math
from math import fabs

from sympy.assumptions.sathandlers import fact

from Game import Game
from Order import Order
from Configuration import *
from operator import attrgetter

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
        if Game.turn == 1:
            self.production = production
            self.current_production = production
        else:
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

    def add_coming_cyborgs(self, new_troop):
        '''
        Add new troops to the factory
        :param new_troop:
        :return:
        '''
        if self.owner == ENNEMY:
            if new_troop.owner == ENNEMY:
                self.cyborgs_coming[FRIEND][new_troop.eta-1] += new_troop.number
            else:
                self.cyborgs_coming[ENNEMY][new_troop.eta - 1] += new_troop.number
        else: # same for player and neutral structure
            if new_troop.owner == ENNEMY:
                self.cyborgs_coming[ENNEMY][new_troop.eta-1] += new_troop.number
            else:
                self.cyborgs_coming[FRIEND][new_troop.eta - 1] += new_troop.number

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
                                                                                                                                        or len(Game.factories_ennemy) == 1) and fact_destination.bomb_eta == -1 and Game.available_bomb != 0

    def is_production_increasing_feasible(self, is_danger_situation):
        '''
        Return true if the factory can increase its production by one
        '''
        return (not (len(Game.factories_owned) == 1)) and self.count_next_increase == 0 and self.stock >= 10 and not is_danger_situation

    def get_estimated_stock(self, nb_turn_production):
        '''
        Return the estimated stock of the factory after nb_turn_production set in parameter
        Take into account time +1 due to the engine game making the factory produce before the battles
        '''

        estimated_production = self.production * (nb_turn_production + 1)
        return estimated_production + self.stock

    def solve_turn(self):
        '''
        Solve the current turn for the factory
        '''

        # Move troops and bombs
        # move troops is simulated by using the first index of the cyborg_coming list
        if self.bomb_eta >= 0:
            self.bomb_eta -= 1

        nb_cyborgs_friends = self.cyborgs_coming[FRIEND][0]
        nb_cyborgs_ennemies = self.cyborgs_coming[ENNEMY][0]

        self.cyborgs_coming[ENNEMY] = self.cyborgs_coming[ENNEMY][1:] + self.cyborgs_coming[ENNEMY][:1]
        self.cyborgs_coming[ENNEMY][len(self.cyborgs_coming[ENNEMY]) - 1] = 0

        self.cyborgs_coming[FRIEND] = self.cyborgs_coming[FRIEND][1:] + self.cyborgs_coming[FRIEND][:1]
        self.cyborgs_coming[FRIEND][len(self.cyborgs_coming[FRIEND]) - 1] = 0

        #Execute orders = troops leaving the factory are not taken into account
        move_orders = [order for order in self.orders if order.type == Order.MOVE or order.type == Order.INC]
        for order in move_orders:
            self.stock -= order.number

            if order.type == Order.INC:
                self.production += 1

                if self.count_zero_prod <= 0:
                    self.current_production = self.production
            else: #Move order
                if order.destination.owner == ENNEMY:
                    if self.owner == ENNEMY:
                        order.destination.cyborgs_coming[FRIEND][self.links[order.destination.f_id].distance-1] = order.number
                    else:
                        order.destination.cyborgs_coming[ENNEMY][self.links[order.destination.f_id].distance - 1] = order.number
                else:
                    if self.owner == FRIEND:
                        order.destination.cyborgs_coming[FRIEND][self.links[order.destination.f_id].distance-1] = order.number
                    else:
                        order.destination.cyborgs_coming[ENNEMY][self.links[order.destination.f_id].distance - 1] = order.number

        # Solve battles (a production takes place before battle)
        if self.owner == 1:
            new_stock = self.current_production + self.stock - nb_cyborgs_ennemies + nb_cyborgs_friends
        elif self.owner == -1:
            new_stock = self.current_production + self.stock - nb_cyborgs_friends + nb_cyborgs_ennemies
        else:
            new_stock = self.stock - nb_cyborgs_friends - nb_cyborgs_ennemies

        owner = self.owner
        if owner == 1 and new_stock < 0:
            owner = -1
        elif owner == -1 and new_stock < 0:
            owner = 1
        elif owner == 0 and new_stock < 0:
            if nb_cyborgs_friends > nb_cyborgs_ennemies:
                owner = 1
            else:
                owner = -1
                # else the factory is still neutral

        # Manage bomb explosion
        if self.bomb_eta == 0:
            self.count_zero_prod = 5

        if self.count_zero_prod > 0:
            self.current_production = 0
        else:
            self.current_production = self.production

        if self.count_zero_prod >= 0:
            self.count_zero_prod -= 1

        # Update the destination factory
        self.owner = owner

        # stock is always positive (negative is positive for new owner)
        self.stock = abs(new_stock)


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
        Compute the number of troops to send to conquer the objective on next ruen as if the distance was one turn
        '''

        # TODO : add a "solver" to simulate the state of the destination factory when the troops will arrive
        # function of the cyborgs already going to the factory, plus new cyborgs coming from the factories closer than self
        # euristic : nb new cyborgs = factory production

        if self.owner == fact_destination.owner :
            nb_cyborg_friends = fact_destination.cyborgs_coming[FRIEND][0]
            nb_cyborg_ennemies = fact_destination.cyborgs_coming[ENNEMY][0]
        elif fact_destination.owner == 0:
            nb_cyborg_friends = fact_destination.cyborgs_coming[FRIEND][0]
            nb_cyborg_ennemies = fact_destination.cyborgs_coming[ENNEMY][0]
        else:
            nb_cyborg_friends = fact_destination.cyborgs_coming[ENNEMY][0]
            nb_cyborg_ennemies = fact_destination.cyborgs_coming[FRIEND][0]

        link = self.links[fact_destination.f_id]

        #if fact_destination.bomb_eta < link.distance and fact_destination.bomb_eta != -1:
        if fact_destination.count_zero_prod > 0:
            #estimated_stock = fact_destination.get_estimated_stock(max(fact_destination.bomb_eta + (NB_PREDICTED_TURN - 5), 0))
            estimated_stock = fact_destination.stock
        else:
            #estimated_stock = fact_destination.get_estimated_stock(NB_PREDICTED_TURN - fact_destination.count_zero_prod)
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
            self.orders.append(Order(Order.INC, self, None, 10))

        if simulated_factory.bomb_eta == 1:
            keep_troops = 0
        else:
            keep_troops = max(delta_agression, 0)

        if self.current_production == 0:
            if len(Game.factories_owned) == 1:
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
                self.orders.append(Order(Order.BOMB, self, destination, 0))
                fact_destination.set_bomb_eta(link.distance)
            else:

                send_troops = self.compute_troops_to_send(fact_destination)
                destination_id = fact_destination.f_id
                destination = fact_destination

                print('send troops : ' + str(send_troops) + ', sendable troops : ' + str(sendable_troops), file=sys.stderr)

                if alternative_path is not None and send_troops < sendable_troops:
                    print('alternative path fact : ' + str(path.intermediate.f_id), file=sys.stderr)

                    intermediate_troop = self.compute_troops_to_send(path.intermediate)
                    send_troops += intermediate_troop
                    destination_id = path.intermediate.f_id
                    destination = path.intermediate

                    print('new troops = ' + str(send_troops), file=sys.stderr)

                send_troops = min(send_troops, sendable_troops)
                if send_troops != 0:
                    # if send_troops <= sendable_troops:

                    self.orders.append(Order(Order.MOVE, self, destination, send_troops))

                    self.stock -= send_troops
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

    def define_conquest_priorities(self):
        '''
        Update the priorities for each destination
        '''

        for key, link in self.links.items():
            destination = link.destination[self.f_id]
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

        estimated_distance = min(self.distance + 1, 20)

        nb_cyborg_ennemies = sum(factory_destination.cyborgs_coming[ENNEMY][estimated_distance:NB_PREDICTED_TURN])
        nb_cyborg_friends = sum(factory_destination.cyborgs_coming[FRIEND][estimated_distance:NB_PREDICTED_TURN])

        estimated_stock = factory_destination.get_estimated_stock(self.distance - factory_destination.count_zero_prod)

        if factory_destination.owner == 1 and nb_cyborg_ennemies > (estimated_stock + nb_cyborg_friends):  # and self.distance < (origin.min_friend_distance + FIRST_EXPLORATION_DELTA)
            # R2 : help your neighbor
            priority = 10 * 1000
            priority += (20 - self.distance) * 10
            priority += factory_destination.production
            priority += nb_cyborg_ennemies

        elif factory_destination.owner == 0 and factory_destination.min_friend_distance < factory_destination.min_ennemy_distance:  # and factory_destination.production > 0
            # R1 : expand around you on factories of interest
            priority = 9 * 1000
            # priority += factory_destination.production * 100
            # priority -= (origin.stock - factory_destination.stock) #Smaller the difference of stock, best it is
            priority += factory_destination.production * 10
            priority += len(sim_origin.alternative_pathes[factory_destination.f_id]) * 100
            priority += 20 - self.distance

        elif factory_destination.owner == 1 and factory_destination.production <= 1 and estimated_stock <= 10:
            # R3 : increase the capacity of your neighbor
            priority = 8 * 1000
            priority += (20 - self.distance) * 10
            priority += 3 - factory_destination.production

        elif factory_destination.owner == -1 and ((factory_destination.bomb_eta != 0 and self.distance == (factory_destination.bomb_eta + 1)) or (factory_destination.count_zero_prod - 1 == self.distance)):
            # R4 : attack your close opponent where he is bombed
            priority = 7 * 1000
            priority += (20 - factory_destination.bomb_eta * 10)
            priority += (5 - factory_destination.count_zero_prod * 10)
            priority += factory_destination.production
        elif factory_destination.owner == -1 and (estimated_stock + nb_cyborg_friends - nb_cyborg_ennemies) < 20 and self.distance < (sim_origin.min_ennemy_distance + FIRST_EXPLORATION_DELTA) and factory_destination.current_production >= 1:
            # R5 : attack your close opponent where he is weak
            priority = 6 * 1000
            # priority += (20 - self.distance) * 100
            # priority += (3-factory_destination.current_production) * 10 - factory_destination.stock
            priority -= estimated_stock + nb_cyborg_friends
            priority += nb_cyborg_ennemies

        elif factory_destination.owner == 0 and factory_destination.production > 0:
            # R6 : expand
            priority = 5 * 1000
            priority += factory_destination.production * 10 - factory_destination.stock
            priority += 20 - self.distance
        elif factory_destination.owner == -1 and nb_cyborg_friends < 20:
            # R7 : attack your ennemy where is weak
            priority = 4 * 1000
            priority += (20 - self.distance) * 10
        elif factory_destination == 1:
            # R8 :defense
            priority = 3 * 1000
            priority += 100 - factory_destination.stock
        elif factory_destination.owner == 0:
            priority = 2 * 1000
        else:
            # R9 :attack
            priority = 1 * 1000
            priority += (20 - self.distance) * 10
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
