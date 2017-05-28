import sys
import math
from operator import attrgetter
from operator import itemgetter
from collections import OrderedDict

FRIEND = 1
PLAYER = 1
ENNEMY = -1
NEUTRAL = 0

NB_CYBORG_INC = 10
DELTA_CONQUER = 1  # to manage function of the production of the factory => prod 3 = 1, other prod = stock + 5

MIN_NB_FACTORIES = 12
COUNT_INCREASE = 0

MAX_FACTORY_CONSIDERED = 6
MAX_DISTANCE_CONSIDERED = 3
NB_SIMU_TURN = 4

MODE_CONQUERING = 0
MODE_CONSOLIDATION = 1
MODE_AGRESSIVE = 2


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

    def clone(self, clone_factories):
        return Troop(self.t_id, self.number, self.eta, self.owner, self.is_bomb, self.link,
                     clone_factories[self.origin.f_id], clone_factories[self.destination.f_id])


class Order:
    '''
    Manage orders expressed by the factories
    '''

    MOVE = 0
    INC = 1
    BOMB = 2
    WAIT = 3

    def __init__(self, action, origin, destination, number):
        self.action = action
        self.number = number
        self.origin = origin
        self.destination = destination

    def to_str(self):
        '''
        Translate the order into string
        :return: translated message
        '''
        if self.action == Order.MOVE:
            msg = 'MOVE ' + str(self.origin.f_id) + ' ' + str(self.destination.f_id) + ' ' + str(self.number)
        elif self.action == Order.INC:
            msg = 'INC ' + str(self.origin.f_id)
        elif self.action == Order.BOMB:
            msg = 'BOMB ' + str(self.origin.f_id) + ' ' + str(self.destination.f_id)
        else:
            msg = 'WAIT'

        return msg

    def clone(self, clone_sender, clone_destination):
        return Order(self.action, self.number, clone_sender, clone_destination)


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

    def clone(self, clone_factories, clone_troops):
        factories_id = list(self.destination.keys())
        clone_fact1 = clone_factories[factories_id[0]]
        clone_fact2 = clone_factories[factories_id[1]]
        clone = Link(self.l_id, clone_fact1, clone_fact2, self.distance)

        for troop in self.troops[clone_fact1.f_id]:
            clone_troop = [clone_troop for clone_troop in clone_troops if clone_troop.t_id == troop.t_id][0]
            clone.troops[clone_fact1.f_id].append(clone_troop)

        for troop in self.troops[clone_fact2.f_id]:
            clone_troop = [clone_troop for clone_troop in clone_troops if clone_troop.t_id == troop.t_id][0]
            clone.troops[clone_fact2.f_id].append(clone_troop)

        return clone

    def get_friendly_troops_for_battle(self, factory):
        '''
        Return the number of friendly troops for the factory ready to engage in a battle
        friendly troop = troops with the same owner as the factory
        except for neutral factory, friendly troops are the troop of the player
        :param factory: factory considered
        :return: number of troops
        '''

        if factory.owner != NEUTRAL:
            match_troops = [troop for troop in self.troops[factory.f_id] if
                            troop.eta == 0 and troop.owner == factory.owner]
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
            match_troops = [troop for troop in self.troops[factory.f_id] if
                            troop.eta == 0 and troop.owner != factory.owner]
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

        if len(match_troops) > 0:
            match_troops.sort(key=attrgetter('eta'))
            return match_troops[0].eta
        else:
            return -1

    def move_troops(self):
        '''
        Move all the troops along the link (reduce ETA of 1)
        Troops with an ETA of 0 are deleted
        return list of deleted troops
        '''

        deleted_troops = []
        for factory_troops in self.troops.values():
            i = 0
            while i < len(factory_troops):
                if factory_troops[i].eta > 0:
                    factory_troops[i].eta -= 1

                    i += 1
                else:
                    deleted_troops.append(factory_troops[i])
                    del factory_troops[i]

        return deleted_troops

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
        self.owner = 0

        self.max_distance = 0
        self.min_distance = 20
        self.max_friend_distance = 0
        self.min_friend_distance = 20
        self.max_ennemy_distance = 0
        self.min_ennemy_distance = 20
        self.max_neutral_distance = 0
        self.min_neutral_distance = 20

        self.nb_friendly_troops = 0
        self.nb_ennemy_troops = 0

        self.index_danger = 0
        self.need_turn = 0
        self.cost = 0
        self.delta = 0  # compute the cumulated ennemy - friend - current_production during simulation

        self.bomb_eta = -1

        self.count_zero_prod = 0
        self.count_next_increase = 0
        self.turn_change_owner = -1

        self.priorities = {}
        self.orders = []

    def clone(self):
        clone = Factory(self.f_id)

        # Duplicate the map but keep the reference to the original link (for now)
        for key, link in self.links.items():
            clone.links[key] = link

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

    def clone_basic_attributes(self):
        clone = Factory(self.f_id)

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
        clone.max_neutral_distance = self.max_neutral_distance
        clone.min_neutral_distance = self.min_neutral_distance

        clone.nb_friendly_troops = self.nb_friendly_troops
        clone.nb_ennemy_troops = self.nb_ennemy_troops

        clone.index_danger = self.index_danger
        clone.need_turn = self.need_turn
        clone.cost = self.cost
        clone.delta = self.delta
        clone.turn_change_owner = self.turn_change_owner

        clone.bomb_eta = self.bomb_eta

        clone.count_zero_prod = self.count_zero_prod
        clone.count_next_increase = self.count_next_increase

        for key, priority in self.priorities.items():
            clone.priorities[key] = priority

        # Clone in second time since there are dependences to solve
        # clone.links = {}
        # clone.orders = []

        return clone

    def set_clone_dependent_attributes(self, clone_factories, clone_links):
        '''
        Clone dependent attributes in the clone of the factory present in clone_factories
        '''
        clone_factory = clone_factories[self.f_id]

        for key, link in self.links.items():
            clone_link = [clone_link for clone_link in clone_links if clone_link.l_id == link.l_id][0]
            clone_factory.links[key] = clone_link

        for order in self.orders:
            clone_destination = [clone_factory for clone_factory in clone_factories if clone_factory.f_id == self.f_id][
                0]
            clone_factory.orders.append(order.clone(clone_factory, clone_destination))

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
                else:
                    self.set_neutral_distances(link.distance)
            else:  # neutral factories are taking into account here to detect if an ennemy base is closer
                if fact_destination.owner == -1:
                    self.set_ennemy_distances(link.distance)
                elif fact_destination.owner == 1:
                    self.set_friend_distances(link.distance)
                else:
                    self.set_neutral_distances(link.distance)

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

    def set_neutral_distances(self, distance):
        if distance > self.max_neutral_distance:
            self.max_neutral_distance = distance

        if distance < self.min_neutral_distance:
            self.min_neutral_distance = distance

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

    def reset_indicators(self):
        self.nb_friendly_troops = 0
        self.nb_ennemy_troops = 0

        self.index_danger = 0
        self.need_turn = 0
        self.cost = 0
        self.delta = 0  # compute the cumulated ennemy - friend - current_production during simulation
        self.turn_change_owner = -1

    def is_production_increasing_feasible(self, is_danger_situation):
        '''
        Return true if the factory can increase its production by one
        '''
        return self.production < 3 and self.count_next_increase == 0 and self.stock >= 10 and not is_danger_situation

    def get_estimated_stock(self, nb_turn_production):
        '''
        Return the estimated stock of the factory after nb_turn_production set in parameter
        Take into account time +1 due to the engine game making the factory produce before the battles
        '''

        estimated_production = self.production * (nb_turn_production + 1)
        return estimated_production + self.stock

    def update_stock(self):
        '''
        Update the factory stock function of the production
        '''
        if self.owner != 0:
            self.stock += self.current_production

    def solve_factory_turn(self):
        '''
        Solve the current turn for the factory
        '''
        # self.update_troops_after_moves()
        # self.emit_orders()
        # self.execute_orders(game) #Execute orders = troops leaving the factory are not taken into account for battle
        self.update_stock()
        self.solve_battle()  # Solve battles (a production takes place before battle)
        self.manage_bomb()

    def solve_battle(self):
        '''
        Solve the battle for the factory
        (a production takes place before battle)
        '''

        current_owner = self.owner

        # if self.owner == FRIEND:
        #    new_stock = self.stock - self.nb_ennemy_troops + self.nb_friendly_troops
        # elif self.owner == ENNEMY:
        #    new_stock = self.stock - self.nb_friendly_troops + self.nb_ennemy_troops
        if current_owner != NEUTRAL:
            new_stock = self.stock + self.nb_friendly_troops - self.nb_ennemy_troops
        else:
            new_stock = self.stock - abs(self.nb_friendly_troops - self.nb_ennemy_troops)

        if current_owner == FRIEND and new_stock < 0:
            self.owner = ENNEMY
        elif current_owner == ENNEMY and new_stock < 0:
            self.owner = FRIEND
        elif current_owner == NEUTRAL and new_stock < 0:
            if self.nb_friendly_troops > self.nb_ennemy_troops:
                self.owner = FRIEND
            else:
                self.owner = ENNEMY
        # else the factory is still neutral

        self.stock = abs(new_stock)  # stock is always positive (negative is positive for new owner)

        if self.owner != current_owner:
            self.delta = 0

        if self.owner != NEUTRAL:
            self.delta += max(self.nb_ennemy_troops - (self.nb_friendly_troops + self.current_production), 0)

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

    def is_bomb_sendable(self, link, fact_destination):
        # TODO : game or factory ???
        return False

    def update_need_for_turn(self, simu=None):
        '''
        Define the number of troops to send this turn
        '''

        if simu is None:
            self_factory = self
        else:
            self_factory = simu.factories[self.f_id]

        if self_factory.owner == FRIEND:
            if self.production < 3:

                self.cost = self_factory.nb_ennemy_troops + 1
                if simu.mode <= MODE_CONSOLIDATION:
                    self.cost += NB_CYBORG_INC
            else:
                self.cost = self_factory.nb_ennemy_troops + 1

            # if self.min_ennemy_distance < MAX_DISTANCE_CONSIDERED:  # == 1:
            #    close_link_ennemies = [link for link in self_factory.links.values() if link.destination[self.f_id].owner == ENNEMY and link.distance < MAX_DISTANCE_CONSIDERED]
            #    for link in close_link_ennemies:
            #        self.cost += link.destination[self.f_id].stock

            self.need_turn = self.cost - (
            self_factory.stock + self_factory.current_production + self_factory.nb_friendly_troops)

        elif self_factory.owner == ENNEMY and self.owner == FRIEND:
            self.cost = self.stock  # keep all the troops
            # self.need_turn = self_factory.stock
            self.need_turn = self_factory.stock + self_factory.current_production + self_factory.nb_friendly_troops - self.nb_ennemy_troops
        elif self_factory.owner == ENNEMY:
            self.cost = 0
            self.need_turn = self_factory.stock + self_factory.current_production + self_factory.nb_friendly_troops + DELTA_CONQUER - self_factory.nb_ennemy_troops
        else:
            if self_factory.production == 0:
                self.cost = 0
                self.need_turn = self_factory.stock - self_factory.nb_friendly_troops + self_factory.nb_ennemy_troops
                if simu.mode <= MODE_CONSOLIDATION:
                    self.cost += NB_CYBORG_INC
            else:
                self.cost = 0
                self.need_turn = self_factory.stock + DELTA_CONQUER - self_factory.nb_friendly_troops + self_factory.nb_ennemy_troops

        self.need_turn = max(self.need_turn, 0)

    def compute_danger_index(self, simu=None):
        '''
        Compute a danger index for the factory
        '''

        if simu is None:
            self_factory = self
        else:
            self_factory = simu.factories[self.f_id]

        if self_factory.min_ennemy_distance > 2 and self_factory.nb_ennemy_troops == 0:
            self.index_danger = 0
        else:
            close_link_ennemies = [link for link in self_factory.links.values() if
                                   link.destination[self.f_id].owner == ENNEMY and link.distance <= 2]
            self.index_danger = (20 - self_factory.min_ennemy_distance * 10)

            for link_ennemy in close_link_ennemies:
                ennemy = link_ennemy.destination[self_factory.f_id]
                self.index_danger += ennemy.stock
                self.index_danger += ennemy.nb_ennemy_troops

            self.index_danger -= self_factory.nb_friendly_troops
            self.index_danger -= self_factory.stock

    def is_danger_situation(self, simu):
        '''
        Return if the factory is in danger
        '''

        if simu is None:
            self_factory = self
        else:
            self_factory = simu.factories[self.f_id]

        # After X turn of simulation the factory has been invaded by the ennemy
        is_danger_situation = (self.owner != self_factory.owner) and (self_factory.owner == ENNEMY)

        is_danger_situation = is_danger_situation or self.bomb_eta == 1

        close_link_ennemies = [link for link in self.links.values() if
                               link.destination[self.f_id].owner == ENNEMY and link.distance < MAX_DISTANCE_CONSIDERED]
        ennemy_stock = 0
        for link in close_link_ennemies:
            ennemy_stock += link.destination[self.f_id].stock

        # Prevent immediate danger that is too late after simulation
        is_danger_situation = is_danger_situation or ennemy_stock > self.stock

        close_link_friends = [link for link in self_factory.links.values() if
                              link.destination[self.f_id].owner == FRIEND]
        is_danger_situation = is_danger_situation or len(close_link_friends) == 0

        # TODO: improve this particular case: simulation is fine but final decision (Inrease + move 5 troops) will give the factory to the ennemy with 3 troops
        # case where increase seems ok in simulation because the simulation does not take account the fact that the factory will have 10 cyborgs less ..
        if self.nb_ennemy_troops != 0:
            is_danger_situation = is_danger_situation or (
            (self.stock + self.nb_friendly_troops + self.current_production - NB_CYBORG_INC) < self.nb_ennemy_troops)

        return is_danger_situation

    def compute_keep_troops(self, sorted_priorities, is_danger_situation, simu=None):
        '''
        Compute the number of troops a factory must keep this turn
        Return the number of sendable troops and the remainig stock
        '''

        if simu is None:
            self_factory = self
        else:
            self_factory = simu.factories[self.f_id]

        if self.f_id == 0:
            print('Game mode = ' + str(simu.mode), file=sys.stderr)

        if self.bomb_eta == 1:
            keep_troops = 0
        else:
            keep_troops = self_factory.delta
            link_friends = [link for link in self_factory.links.values() if link.destination[self.f_id].owner == FRIEND]
            if self.production < 3:
                if (self.production == 0 and len(link_friends) > 0) \
                        or (self.production <= 2 and not is_danger_situation):
                    if simu.mode <= MODE_CONSOLIDATION:
                        keep_troops += NB_CYBORG_INC

        return min(keep_troops, self.stock)

    def emit_orders(self, simu=None):
        '''
        Define the orders emitted by owned factory
        '''
        print('factory : ' + str(self.f_id), file=sys.stderr)

        if simu is None:
            self_factory = self
        else:
            self_factory = simu.factories[self.f_id]

        factory_stock = self.stock

        self.define_conquest_priorities(simu)
        sorted_priorities = OrderedDict(sorted(self.priorities.items(), key=itemgetter(1), reverse=True))

        is_danger_situation = self.is_danger_situation(simu)
        keep_troops = self.compute_keep_troops(sorted_priorities, is_danger_situation, simu)

        print(str(self.f_id) + ' => d: ' + str(is_danger_situation) + ', k: ' + str(keep_troops) + ', n: ' + str(
            self.need_turn) + ', c: ' + str(self.cost), file=sys.stderr)
        if not is_danger_situation and (keep_troops - 10 >= 0):
            # factory_stock -= 10
            if simu.mode <= MODE_CONSOLIDATION:
                self.orders.append(Order(Order.INC, self, self, 10))

        sendable_troops = max(factory_stock - keep_troops, 0)

        for prio_factory_id, priority in sorted_priorities.items():
            link = self_factory.links[prio_factory_id]
            fact_destination = link.destination[self.f_id]

            if fact_destination.need_turn > 0:

                send_troops = fact_destination.need_turn
                destination_id = fact_destination.f_id
                destination = fact_destination

                if link.distance > MAX_DISTANCE_CONSIDERED and priority < 12000:

                    # print('get intermediate for ' + str(fact_destination.f_id), file=sys.stderr)
                    destination = self_factory.get_intermediate(link, fact_destination)

                    if destination.need_turn > 0:
                        send_troops += max(min(destination.need_turn, sendable_troops - send_troops), 0)

                        # print('optimization ' + str(fact_destination.f_id) + ' becomes ' + str(destination.f_id), file=sys.stderr)

                send_troops = min(send_troops, sendable_troops)

                print('T: ' + str(fact_destination.f_id) + ' - P: ' + str(priority) + ' - D: ' + str(link.distance),
                      ' - S: ' + str(send_troops) + '/' + str(sendable_troops), file=sys.stderr)

                if send_troops != 0:
                    # if send_troops <= sendable_troops:

                    self.orders.append(Order(Order.MOVE, self, destination, send_troops))

                    factory_stock -= send_troops
                    sendable_troops -= send_troops

                    destination.need_turn -= sendable_troops
                    destination.need_turn = max(destination.need_turn, 0)

                    if sendable_troops == 0:
                        pass

        if sendable_troops != 0 and self.production == 3 and not is_danger_situation:
            link_friend_factories = [link for link in self.links.values() if
                                     link.destination[self.f_id].owner == FRIEND]
            link_friend_factories.sort(key=lambda link: link.destination[self.f_id].index_danger, reverse=True)

            if len(link_friend_factories) != 0:
                destination = link_friend_factories[0].destination[self.f_id]
                if self.index_danger < destination.index_danger:
                    self.orders.append(Order(Order.MOVE, self, destination, sendable_troops))

                    destination.need_turn -= sendable_troops
                    destination.need_turn = max(destination.need_turn, 0)

        if len(self.orders) == 0:
            self.orders.append(Order(Order.WAIT, self, self, 0))

    def get_intermediate(self, link, target):
        '''
        Return the closest intermediate from the factory to reach the target
        '''

        friend_intermediate = target
        ennemy_intermediate = target

        for key, link_int in self.links.items():
            intermediate = link_int.destination[self.f_id]

            if intermediate.f_id != target.f_id and intermediate.links[target.f_id].distance < link.distance:
                if intermediate.owner != FRIEND:
                    if intermediate.links[self.f_id].distance + 1 <= ennemy_intermediate.links[self.f_id].distance:
                        if ennemy_intermediate.f_id == target.f_id:
                            ennemy_intermediate = intermediate
                        elif intermediate.links[target.f_id].distance < ennemy_intermediate.links[target.f_id].distance:
                            ennemy_intermediate = intermediate

                else:
                    if intermediate.links[self.f_id].distance + 1 <= friend_intermediate.links[self.f_id].distance:
                        if friend_intermediate.f_id == target.f_id:
                            friend_intermediate = intermediate
                        elif intermediate.links[target.f_id].distance < friend_intermediate.links[target.f_id].distance:
                            friend_intermediate = intermediate

        destination = target
        if friend_intermediate.f_id == target.f_id:
            if ennemy_intermediate.f_id != target.f_id and ennemy_intermediate.links[self.f_id].distance:
                destination = ennemy_intermediate

        elif ennemy_intermediate.f_id == target.f_id:
            if friend_intermediate.f_id != target.f_id and friend_intermediate.links[self.f_id].distance:
                destination = friend_intermediate

        else:
            if friend_intermediate.links[self.f_id].distance > ennemy_intermediate.links[self.f_id].distance \
                    and ennemy_intermediate.links[self.f_id].distance < self.links[target.f_id].distance:
                destination = ennemy_intermediate
            elif friend_intermediate.links[self.f_id].distance < self.links[target.f_id].distance:
                destination = friend_intermediate

        return destination

    def define_conquest_priorities(self, simu):
        '''
        Update the priorities for each destination
        '''

        for key, link in self.links.items():
            self.priorities[key] = self.define_conquest_priority(link, simu)

    def define_conquest_priority(self, link, simu):
        '''
        Compute the priority for the factory set as origin
        to conquer the factory at the other side of the link
        Priority goes as :
        - The factory is not owned > ennemy > owned
        - Higher factory production is the better
        - Closer the factory is the better
        @param origin : factory from where the cyborgs are emitted from

        # R1 : attack your close opponent where he is bombed
        # R2 : help your ex friends
        # R3 : help your neighbor
        # R4 : help your neighbor to increase production to level 2
        # R5 : expand around you on factories of interest
        # R6 : attack your close opponent where he is weak
        # R7 : expand on neutral factories
        # R8 : attack ennemies

        '''

        priorities = simu.conquest_priorities
        selected_priorities = []

        present_destination = link.destination[self.f_id]
        simu_destination = simu.factories[present_destination.f_id]

        if self.f_id == 5 and present_destination.f_id == 2:
            print('bomb_eta: ' + str(present_destination.bomb_eta) + ', distance: ' + str(link.distance),
                  file=sys.stderr)

        if simu_destination.owner == ENNEMY \
                and (((link.distance - present_destination.bomb_eta) < 5 and (
                    link.distance - present_destination.bomb_eta) >= 0 and present_destination.bomb_eta >= 0) \
                             or ((
                                     link.distance - present_destination.count_zero_prod) == 1 and present_destination.count_zero_prod > 0)):
            # and (((link.distance - simu_destination.bomb_eta) < 5 and (link.distance - simu_destination.bomb_eta) > 0 and simu_destination.bomb_eta >= 0) \
            # or ((link.distance - simu_destination.count_zero_prod) == 1 and simu_destination.count_zero_prod > 0)):


            # R1 : attack your close opponent where he is bombed
            priority = priorities[0] * 1000
            priority += simu_destination.bomb_eta * 10
            priority += simu_destination.count_zero_prod * 10
            priority += simu_destination.production * 100
            priority += simu_destination.nb_friendly_troops * 10
            priority += (20 - link.distance) * 10
            selected_priorities.append(priority)

        if simu_destination.owner != present_destination.owner and simu_destination.owner == ENNEMY and present_destination == FRIEND:
            # R2 : help your ex friends
            priority = priorities[1] * 1000
            priority += simu_destination.production * 10
            priority += 20 - link.distance
            selected_priorities.append(priority)

        if simu_destination.owner == FRIEND and (((
                                                          simu_destination.stock + simu_destination.nb_friendly_troops + simu_destination.current_production) < simu_destination.nb_ennemy_troops)):  # or simu_destination.min_ennemy_distance == 1):
            # R3 : help your neighbor
            priority = priorities[2] * 1000
            priority += simu_destination.production
            priority += simu_destination.min_ennemy_distance
            selected_priorities.append(priority)

        if simu_destination.owner == FRIEND and (
                self.production > simu_destination.production or self.bomb_eta == 1) and simu_destination.production <= 1 and simu_destination.nb_ennemy_troops == 0:
            # R4 : help your neighbor to increase production to level 2

            priority = priorities[3] * 1000
            priority += simu_destination.production * 100
            priority += simu_destination.min_ennemy_distance
            selected_priorities.append(priority)

        if simu_destination.owner == NEUTRAL:
            # R5 : expand around you on factories of interest

            priority = priorities[4] * 1000
            priority += simu_destination.production * 10
            # priority += simu_destination.min_ennemy_distance * 5
            priority += (20 - link.distance) * 10
            priority += simu_destination.min_ennemy_distance
            priority -= simu_destination.stock
            selected_priorities.append(priority)

        if simu_destination.owner == ENNEMY and simu_destination.bomb_eta <= 0:  # and (simu_destination.nb_friendly_troops + self.stock) > (simu_destination.stock + simu_destination.nb_ennemy_troops + simu_destination.current_production):
            # R6 : attack your close opponent where he is weak

            priority = priorities[5] * 1000
            # priority += simu_destination.production * 100
            priority += simu_destination.nb_friendly_troops
            priority -= simu_destination.nb_ennemy_troops
            priority -= simu_destination.stock * 10
            priority += (3 - simu_destination.current_production) * 10
            priority -= simu_destination.production * 10
            priority += (20 - link.distance) * 10
            selected_priorities.append(priority)

        if simu_destination.owner == NEUTRAL:
            # R7 : expand:
            priority = priorities[6] * 1000
            priority += simu_destination.production * 100
            priority += simu_destination.min_ennemy_distance
            selected_priorities.append(priority)

        if simu_destination.owner == ENNEMY and simu_destination.bomb_eta <= 0:
            # R8 : attack:
            priority = priorities[7] * 1000
            priority += simu_destination.production * 100
            priority += (20 - link.distance) * 10
            selected_priorities.append(priority)
        else:
            selected_priorities.append(0)

        priority = max(selected_priorities)
        if link.distance > MAX_DISTANCE_CONSIDERED and priority < 12000:
            priority = round(priority / 10)

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
        bomb_eta = self.bomb_eta

        for link in self.links.values():
            self.nb_friendly_troops += link.get_friendly_troops_for_battle(self)
            self.nb_ennemy_troops += link.get_ennemy_troops_for_battle(self)

            new_bomb_eta = link.get_bomb_eta(self)
            if new_bomb_eta != -1:

                if bomb_eta == -1:
                    bomb_eta = new_bomb_eta
                else:
                    bomb_eta = min(new_bomb_eta, bomb_eta)

        if bomb_eta != -1:
            if self.bomb_eta == -1:
                self.bomb_eta = bomb_eta
            elif self.bomb_eta == bomb_eta:
                self.bomb_eta = -1
            else:
                self.bomb_eta = min(self.bomb_eta, bomb_eta)
        else:
            self.bomb_eta = -1

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

            elif order.action == Order.MOVE:  # Move order
                self.links[order.destination.f_id].add_troops(self, order.destination, order.number, False, game)
            else:  # Bomb order
                self.links[order.destination.f_id].add_troops(self, order.destination, 0, True, game)

        self.orders.clear()


class Game:
    '''
    Manage all the global states of the game
    '''

    def __init__(self):
        self.factories = []
        self.factories_owned = []
        self.factories_ennemy = []

        self.links = []

        self.troops = []
        self.troops_owned = []
        self.troops_ennemy = []

        self.available_bomb = 2

        self.delta_prod = 0
        self.prod_ennemy = 0
        self.prod_friend = 0
        self.turn_equality = 0

        self.mode = MODE_CONSOLIDATION
        self.conquest_priorities = [12, 11, 10, 9, 8, 7, 6, 5]

        self.turn = 1

    def initialize_game(self, factory_count, link_count):
        '''
        Initialize the game at the beginning of the party
        :return:
        '''

        self.factory_count = factory_count
        self.link_count = link_count  # the number of links between factories
        self.turn = 1

    def create_factories(self):
        for i in range(self.factory_count):
            self.factories.append(Factory(i))

    def add_link(self, factory_1, factory_2, distance):
        link = Link(i, self.factories[factory_1], self.factories[factory_2], distance)
        self.factories[factory_1].links[factory_2] = link
        self.factories[factory_2].links[factory_1] = link
        self.links.append(link)

    def reset(self, turn=-1):
        '''
        Rest the state of the game before getting the information of the new turn
        '''
        self.factories_owned.clear()
        self.factories_ennemy.clear()

        for factory in self.factories:
            # factory.decrease_bombs()
            factory.restore_productivity()
            factory.reset_distances()
            factory.reset_orders()

            # put all the ETA (except bomb to player) at 0 at the beginning of the turn
        # all troops with eta 0 at the end of initialization have to be deleted (including bomb to player)
        for troop in self.troops:
            if not (troop.owner == ENNEMY and troop.is_bomb) or (troop.is_bomb and troop.eta == 1):
                troop.eta = 0

        if turn != -1:
            self.turn = turn

    def get_min_distance_in_level(self):
        distance = 20
        for factory in self.factories_owned:
            if factory.min_ennemy_distance < distance:
                distance = factory.min_ennemy_distance

            if factory.min_neutral_distance < distance:
                distance = factory.min_neutral_distance

        return distance

    def initialize_factories(self):
        '''
        Initialize the state of the factories
        '''

        for factory in self.factories:
            factory.set_distances()

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

                new_troop = Troop(entity_id, arg_4, arg_5, arg_1, False, factory_origin.links[arg_3], factory_origin,
                                  factory_destination)

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
                    factory_destination = self.estimate_target(factory_origin)
                    link = factory_origin.links[factory_destination.f_id]
                    bomb_eta = link.distance
                else:
                    factory_destination = self.factories[arg_3]
                    link = factory_origin.links[arg_3]
                    bomb_eta = arg_4

                new_troop = Troop(entity_id, 0, bomb_eta, arg_1, True, link, factory_origin, factory_destination)

                self.troops.append(new_troop)
                factory_destination.set_bomb_eta(bomb_eta)
                factory_origin.sent_troops(factory_destination.f_id, new_troop)

                if factory_destination.f_id == 1:
                    print('target bomb eta = ' + str(factory_destination.bomb_eta), file=sys.stderr)

                if arg_1 == ENNEMY:
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
            temp = sorted(self.factories_owned,
                          key=lambda factory: (factory.bomb_eta, -factory.production, -factory.stock))
            target = temp[0]

        print('TARGET : ' + str(target.f_id), file=sys.stderr)

        return target

    def send_bomb_order(self, simulated_game):
        '''
        Manage to send a bomb if possible
        '''

        if self.available_bomb > 0:
            target = None
            sorted_factories = sorted(simulated_game.factories_ennemy, key=lambda factory: factory.production,
                                      reverse=True)
            max_ennemy_poduction = max(factory.production for factory in simulated_game.factories_ennemy)

            # TODO : improve bomb to send only if time in simu is less or equal than distance between friend factory and ennemy factory
            for factory in sorted_factories:

                # Improve bomb to not send to prod = 1 except if prod 1 is the max on all ennemies factories
                if (
                                    max_ennemy_poduction <= 1 and factory.production == 1 and factory.stock >= 0 and factory.bomb_eta <= 0 and factory.count_zero_prod <= 0) \
                        or (
                                            max_ennemy_poduction >= 2 and factory.production >= 2 and factory.stock >= 0 and factory.bomb_eta <= 0 and factory.count_zero_prod <= 0):
                    # if (factory.production >= 1 and factory.stock >= 0) and factory.bomb_eta <= 0 and factory.count_zero_prod <= 0:
                    if (len(self.factories) > MIN_NB_FACTORIES and len(
                            self.factories_ennemy) == 1 and factory.production > 1) \
                            or (self.turn >= 2):
                        target = factory
                        break

            if target is not None:
                sorted_links = sorted(target.links.values(), key=lambda link: link.distance)
                link_friend_factories = [link for link in sorted_links if link.destination[
                    target.f_id].owner == FRIEND and link.distance > target.turn_change_owner]

                if len(link_friend_factories) != 0:
                    closest_friend_factory = link_friend_factories[0].destination[target.f_id]

                    # Test if the factory is already a friend, otherwise wait until it becomes a friend
                    if self.factories[closest_friend_factory.f_id].owner == FRIEND:
                        self.available_bomb -= 1
                        return Order(Order.BOMB, closest_friend_factory, target, 0)

        return None

    def send_orders_to_engine(self):
        msg = ''
        for factory in self.factories_owned:
            msg += factory.generate_message_orders()

        previous_prod_ennemy = self.prod_ennemy
        previous_prod_friend = self.prod_friend
        previous_delta = self.delta_prod

        self.prod_ennemy = sum(factory.current_production for factory in self.factories_ennemy)
        self.prod_friend = sum(factory.current_production for factory in self.factories_owned)

        self.delta_prod += self.prod_friend - self.prod_ennemy

        stock_ennemy = sum(factory.stock for factory in self.factories_ennemy)
        stock_friend = sum(factory.stock for factory in self.factories_owned)

        len_field = 50

        msg_prod = 'MSG Prod: ' + str(self.prod_friend) + ' vs ' + str(self.prod_ennemy) + ' => ' + str(self.delta_prod)
        filler = '                                                        '
        msg_prod += filler[0:len_field - len(msg_prod) - 4]
        msg_prod += 'Stock: ' + str(stock_friend) + ' vs ' + str(stock_ennemy)

        if previous_delta == self.delta_prod and self.delta_prod == 0 and previous_prod_friend == self.prod_friend:
            self.turn_equality += 1
        else:
            self.turn_equality = 0

        if len(self.factories_owned) > 0:
            return msg + msg_prod
        else:
            return 'WAIT' + ';' + msg_prod

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

        # 1) Move existing troops and bombs
        deleted_troops = []
        for link in self.links:
            deleted_troops.extend(link.move_troops())

        for troop in deleted_troops:
            self.troops.remove(troop)

        # 2) Execute user orders
        # 3) Produce new cyborgs in all factories
        # 4) Solve battles
        # 5) Make the bombs explode
        self.factories_owned.clear()
        self.factories_ennemy.clear()

        for factory in self.factories:
            # if factory.owner != 0:

            present_owner = factory.owner

            factory.update_troops_after_moves()
            factory.update_need_for_turn(self)
            factory.compute_danger_index()
            factory.solve_factory_turn()

            if factory.owner == FRIEND:
                self.factories_owned.append(factory)
            elif factory.owner == ENNEMY:
                self.factories_ennemy.append(factory)

            if present_owner != factory.owner:
                factory.turn_change_owner = self.turn

        # 6) Check end conditions
        # TODO ?

        self.turn += 1

    def consolidate_inputs(self):
        for factory in self.factories:
            factory.set_distances()

        # Delete from link old troops with eta == 0 (no more updated by inputs)
        nb_deleted_troops = 0
        for link in self.links:
            for factory_troops in link.troops.values():
                troops_eta_0 = [troop for troop in factory_troops if troop.eta == 0]
                nb_deleted_troops += len(troops_eta_0)
                for i in range(len(troops_eta_0)):
                    factory_troops.remove(troops_eta_0[i])

        # Delete from troops old troops with eta == 0 (no more updated by inputs)
        troops_eta_0 = [troop for troop in self.troops if troop.eta == 0]
        nb_deleted_troops += len(troops_eta_0)
        for i in range(len(troops_eta_0)):
            self.troops.remove(troops_eta_0[i])

    def solve_turn(self, simulated_game):

        print('GAME SOLVE TURN', file=sys.stderr)

        for factory in self.factories_ennemy:
            factory.update_troops_after_moves()
            factory.update_need_for_turn(simulated_game)

        for factory in self.factories_owned:
            factory.update_troops_after_moves()
            factory.update_need_for_turn(simulated_game)
            factory.compute_danger_index(simulated_game)
            factory.emit_orders(simulated_game)

        # Post treatment to manage launching bombs - replace other action to the same destination factory
        order = self.send_bomb_order(simulated_game)
        if order is not None:
            match_order = [f_order for f_order in self.factories[order.origin.f_id].orders if
                           f_order.destination.f_id == order.destination.f_id]

            if len(match_order) != 0:
                match_order[0].action = order.action
                match_order[0].number = order.number
            else:
                self.factories[order.origin.f_id].orders.append(order)

        # TODO : Post treatment to optimize orders

        print(self.send_orders_to_engine())
        self.turn += 1

    def next_id_troop(self):
        if len(self.troops) == 0:
            return 0
        else:
            return max(troop.t_id for troop in self.troops) + 1

    def set_game_mode(self):
        '''
        Define the IA mode depending of the global state of the game

        List of rules for factories:
        # R1 : attack your close opponent where he is bombed
        # R2 : help your ex friends
        # R3 : help your neighbor
        # R4 : help your neighbor to increase production to level 2
        # R5 : expand around you on factories of interest
        # R6 : attack your close opponent where he is weak
        # R7 : expand on neutral factories
        # R8 : attack ennemies
        '''
        prod_ennemy = sum(factory.current_production for factory in self.factories_ennemy)
        prod_friend = sum(factory.current_production for factory in self.factories_owned)

        if prod_friend < prod_ennemy:
            self.mode = MODE_CONQUERING
            self.conquest_priorities = [12, 11, 10, 8, 9, 6, 7, 5]
        elif prod_friend < prod_ennemy:
            self.mode = MODE_CONSOLIDATION
            self.conquest_priorities = [12, 11, 10, 9, 8, 7, 6, 5]
        else:
            self.mode = MODE_AGRESSIVE
            self.conquest_priorities = [12, 11, 10, 7, 8, 9, 5, 6]

    def clone(self):
        clone = Game()

        for factory in game.factories:
            clone_factory = factory.clone_basic_attributes()
            clone.factories.append(clone_factory)

            if clone_factory.owner == FRIEND:
                clone.factories_owned.append(clone_factory)
            elif clone_factory.owner == ENNEMY:
                clone.factories_ennemy.append(clone_factory)

        for troop in game.troops:
            clone_troop = troop.clone(clone.factories)

            clone.troops.append(clone_troop)
            if clone_troop.owner == FRIEND:
                clone.troops_owned.append(clone_troop)
            elif clone_troop.owner == ENNEMY:
                clone.troops_ennemy.append(clone_troop)

        for link in game.links:
            clone_link = link.clone(clone.factories, clone.troops)
            clone.links.append(clone_link)

        for factory in self.factories:
            factory.set_clone_dependent_attributes(clone.factories, clone.links)

        clone.available_bomb = self.available_bomb
        clone.delta_prod = self.delta_prod
        clone.prod_ennemy = self.prod_ennemy
        clone.prod_friend = self.prod_friend
        clone.turn_equality = self.turn_equality

        clone.turn = 0  # self.turn

        return clone


factory_count = int(input())  # the number of factories
link_count = int(input())  # the number of links between factories

game = Game()
game.initialize_game(factory_count, link_count)
game.create_factories()

for i in range(link_count):
    factory_1, factory_2, distance = [int(j) for j in input().split()]
    game.add_link(factory_1, factory_2, distance)

game.initialize_factories()
# game loop
while True:
    game.reset()

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

    game.consolidate_inputs()

    simu = game.clone()

    MAX_DISTANCE_CONSIDERED = max(game.get_min_distance_in_level(), MAX_DISTANCE_CONSIDERED)
    NB_SIMU_TURN = MAX_DISTANCE_CONSIDERED + 1

    for i in range(NB_SIMU_TURN):
        simu.simulate_turn()

    simu.set_game_mode()

    game.solve_turn(simu)