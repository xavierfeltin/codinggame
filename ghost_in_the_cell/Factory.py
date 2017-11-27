import sys

from Game import Game
from Order import Order
from Configuration import *
from Path import Path
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
        self.set_distances()

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
            self.orders.append(Order(Order.INC, self, self, 10))

        if self.bomb_eta == 1:
            keep_troops = 0
        else:
            keep_troops = max(delta_agression, 0)

        sendable_troops = max(factory_stock - keep_troops, 0)

        sorted_priorities = [(k, self.priorities[k]) for k in sorted(self.priorities, key=self.priorities.get, reverse=True)]

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
            self.orders.append(Order(Order.WAIT, self, self, 0))

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

        if link.distance > MAX_DISTANCE_CONSIDERED:
            priority = round(priority/100)

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

        move_orders = [order for order in self.orders if order.action == Order.MOVE or order.action == Order.INC]
        for order in move_orders:
            self.stock -= order.number
            if order.action == Order.INC:
                self.production += 1
                self.count_next_increase = COUNT_INCREASE
                if self.count_zero_prod <= 0:
                    self.current_production = self.production

            elif order.action == Order.MOVE:  #Move order
                self.links[order.destination.f_id].add_troops(self, order.destination, order.number, False,game)
            else: #Bomb order
                self.links[order.destination.f_id].add_troops(self, order.destination, 0, True,game)

        self.orders.clear()