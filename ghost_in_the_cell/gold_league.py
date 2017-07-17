import sys
import math
import time
from operator import attrgetter
from operator import itemgetter
from collections import OrderedDict

FRIEND = 1
PLAYER = 1
ENNEMY = -1
NEUTRAL = 0

NB_CYBORG_INC = 10
DELTA_CONQUER = 1  # to manage function of the production of the factory => prod 3 = 1, other prod = stock + 5

MIN_NB_FACTORIES = 7
COUNT_INCREASE = 0

MAX_FACTORY_CONSIDERED = 6
MAX_DISTANCE_CONSIDERED = 3
NB_SIMU_TURN = 4

MODE_CONSOLIDATION = 0
MODE_CONQUERING = 1
MODE_AGRESSIVE = 2

class Input:
    def __init__(self, entity_type, entity_id, arg1, arg2, arg3, arg4, arg5):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.arg1 = arg1
        self.arg2 = arg2
        self.arg3 = arg3
        self.arg4 = arg4
        self.arg5 = arg5
    
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
        self.is_central = False
        
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
        self.is_central = False

        self.index_danger = 0
        self.need_turn = 0        
        self.delta = 0  # compute the cumulated ennemy - friend - current_production during simulation
        self.sendable_troops = 0

        self.bomb_eta = -1

        self.count_zero_prod = 0
        self.count_next_increase = 0
        self.turn_change_owner = -1
        self.present_owner = self.owner
        
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
        clone.present_owner = self.present_owner

        clone.max_distance = self.max_distance
        clone.min_distance = self.min_distance
        clone.max_friend_distance = self.max_friend_distance
        clone.min_friend_distance = self.min_friend_distance
        clone.max_ennemy_distance = self.max_ennemy_distance
        clone.min_ennemy_distance = self.min_ennemy_distance
        clone.max_neutral_distance = self.max_neutral_distance
        clone.min_neutral_distance = self.min_neutral_distance
        clone.is_central = self.is_central

        clone.nb_friendly_troops = self.nb_friendly_troops
        clone.nb_ennemy_troops = self.nb_ennemy_troops

        clone.index_danger = self.index_danger
        clone.need_turn = self.need_turn        
        clone.delta = self.delta
        clone.turn_change_owner = self.turn_change_owner
        
        clone.sendable_troops = self.sendable_troops

        clone.bomb_eta = self.bomb_eta

        clone.count_zero_prod = self.count_zero_prod
        clone.count_next_increase = self.count_next_increase

        for key, priority in self.priorities.items():
            clone.priorities[key] = priority

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
        self.present_owner = owner

    def set_distances(self):
        self.max_distance = 0
        self.min_distance = 20
        
        for key, link in self.links.items():
            if link.distance > self.max_distance:
                self.max_distance = link.distance

            if link.distance < self.min_distance:
                self.min_distance = link.distance

            fact_destination = link.destination[self.f_id]
            if self.owner == ENNEMY:
                if fact_destination.owner == ENNEMY:
                    self.set_friend_distances(link.distance)
                elif fact_destination.owner == FRIEND:
                    self.set_ennemy_distances(link.distance)
                else:
                    self.set_neutral_distances(link.distance)
            else:  # neutral factories are taking into account here to detect if an ennemy base is closer
                if fact_destination.owner == ENNEMY:
                    self.set_ennemy_distances(link.distance)
                elif fact_destination.owner == FRIEND:
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
        self.sendable_troops = 0

        self.index_danger = 0
        self.need_turn = 0        
        self.delta = 0  # compute the cumulated ennemy - friend - current_production during simulation
        self.turn_change_owner = -1
        self.present_owner = self.owner

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

        if self.owner != NEUTRAL:
            if self.owner == self.present_owner or (self.owner != self.present_owner and current_owner == self.present_owner):
                self.delta += max(self.nb_ennemy_troops - (self.nb_friendly_troops + self.current_production), 0)
            elif self.present_owner != NEUTRAL and self.owner != self.present_owner and self.owner == current_owner:
                self.delta += max((self.nb_friendly_troops + self.current_production) - self.nb_ennemy_troops, 0) 

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
        Define the need of the factory to face the situation in SIMULATED_TURN
        '''

        if simu is None:
            self_factory = self
        else:
            self_factory = simu.factories[self.f_id]


        if self_factory.owner == FRIEND:            
            #Compute to face the ennemies after the simulation period and do a possible increase
            self.need_turn = self_factory.nb_ennemy_troops - (self_factory.stock + self_factory.current_production + self_factory.nb_friendly_troops)                                  
        
        elif self_factory.owner == ENNEMY and self.owner == FRIEND:
            #Compute to retake the factory from the ennemies after the simulation period
            self.need_turn = self_factory.stock + self_factory.current_production + self_factory.nb_friendly_troops + DELTA_CONQUER - self.nb_ennemy_troops
        
        elif self_factory.owner == ENNEMY:
            #Compute to take the factory from the ennemies after the simulation period
            self.need_turn = self_factory.stock + self_factory.current_production + self_factory.nb_friendly_troops + DELTA_CONQUER - self.nb_ennemy_troops
        else:
            #Compute to take the neutral factory and do some possible increase
            self.need_turn = self_factory.stock - self_factory.nb_friendly_troops + self_factory.nb_ennemy_troops + DELTA_CONQUER            
        
        self.need_turn +=  self_factory.delta
        
        if (self_factory.owner == FRIEND and self.need_turn <= 0 and self_factory.production < 3) \
        or (self_factory.owner == NEUTRAL and self.need_turn <= 1 and self_factory.production == 0):                
            if simu.mode == MODE_CONSOLIDATION:                
                self.need_turn += NB_CYBORG_INC
        
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

        close_link_ennemies = [link for link in self.links.values() if link.destination[self.f_id].owner == ENNEMY and link.distance < MAX_DISTANCE_CONSIDERED]        
        ennemy_stock = 0
        for link in close_link_ennemies:
            ennemy_stock += link.destination[self.f_id].stock

        # Prevent immediate danger that is too late after simulation
        is_danger_situation = is_danger_situation or ennemy_stock > self.stock

        close_link_friends = [link for link in self_factory.links.values() if
                              link.destination[self.f_id].owner == FRIEND]
                              
        is_danger_situation = is_danger_situation or len(close_link_friends) == 0

        is_danger_situation = is_danger_situation or (self_factory.delta != 0)        
                        
        return is_danger_situation

    def compute_keep_troops(self, sorted_priorities, is_danger_situation, simu=None):
        '''
        Compute the number of troops a factory must keep this turn
        Return the number of sendable troops and the remainig stock
        The troops kept are necessary to make more probable the simulation
        '''

        if simu is None:
            self_factory = self
        else:
            self_factory = simu.factories[self.f_id]

        if self.bomb_eta >= 1:
            return 0
            
            #If after the bomb, the factory has the possibility to resist some cyborgs coming just after
            #keep the stock to avoid losing the factory
            #Except if the factory does not have a production (easy to retake)
            
            #if (self_factory.delta > 0 and self_factory.stock < 0) \
            #or self_factory.delta == 0 \
            #or self_factory.production == 0:
            #    keep_troops = 0
            #else:
            #    keep_troops = self.stock
        else:
            keep_troops = self_factory.delta
            
            link_friends = [link for link in self_factory.links.values() if link.destination[self.f_id].owner == FRIEND]
            if self.production < 3:
                if ((self.production == 0 and len(link_friends) > 0) or (self.production < 3)) and not is_danger_situation:                    
                    if simu.mode == MODE_CONSOLIDATION:
                        keep_troops += NB_CYBORG_INC
           
            sorted_priorities = OrderedDict(sorted(self.priorities.items(), key=itemgetter(1), reverse=True))
            for f_id, priority in sorted_priorities.items():
                if priority >= 11000 and (keep_troops - self_factory.delta) > 0 and self.links[f_id].distance <= MAX_DISTANCE_CONSIDERED:                
                    #keep_troops -= min(self.links[f_id].destination[self.f_id].need_turn, self.delta)
                    keep_troops -= self.links[f_id].destination[self.f_id].need_turn
                    keep_troops = max(keep_troops, self_factory.delta)                                        
                else:
                    break
                
            return min(max(keep_troops, self_factory.delta), self.stock)

    def emit_orders(self, simu=None):
        '''
        Define the orders emitted by owned factory
        '''        

        self_factory = self
        simu_factory = simu.factories[self.f_id]

        factory_stock = self.stock
                
        sorted_priorities = OrderedDict(sorted(self.priorities.items(), key=itemgetter(1), reverse=True))

        is_danger_situation = self.is_danger_situation(simu)
        keep_troops = self.compute_keep_troops(sorted_priorities, is_danger_situation, simu)

        print('F: ' + str(self.f_id) + ', danger: ' + str(is_danger_situation) + ', delta: ' +  str(simu_factory.delta) + ', keep: ' + str(keep_troops) + ', need: ' + str(
            self_factory.need_turn), file=sys.stderr)
        
        if not is_danger_situation and keep_troops >= 10 and self_factory.need_turn == 0 : #and (simu.nb_friend_troops - simu.nb_ennemy_troops) > 5                        
            #if simu.nb_friend_troops - simu.nb_ennemy_troops >= 10:
            self.orders.append(Order(Order.INC, self, self, 10))

        self.sendable_troops = max(factory_stock - keep_troops, 0)

        for prio_factory_id, priority in sorted_priorities.items():
            
            if priority >= 1000:
            
                link = self_factory.links[prio_factory_id]
                fact_destination = link.destination[self.f_id]
    
                #if fact_destination.need_turn == 0 and fact_destination.owner == NEUTRAL:
                #    send_troops = 1
                #else:
                #    send_troops = fact_destination.need_turn
                send_troops = fact_destination.need_turn
                                
                send_troops = min(send_troops, self.sendable_troops)                    
                                
                ##XF fact_destination.need_turn -= send_troops
                ##XF fact_destination.need_turn = max(fact_destination.need_turn, 0)
                self.sendable_troops -= send_troops
                                                                                                                                    
                destination = self_factory.get_intermediate(link, fact_destination) 
                
                if destination.f_id != fact_destination.f_id:
                    #if destination.need_turn == 0 and destination.owner == NEUTRAL:
                    #    intermediate_send_troops = 1
                    #elif destination.need_turn > 0:
                    #    intermediate_send_troops = max(min(destination.need_turn, self.sendable_troops - send_troops), 0)
                    #else:
                    #    intermediate_send_troops = 0
                    intermediate_send_troops = max(min(destination.need_turn, self.sendable_troops - send_troops), 0)    
                        
                        
                    intermediate_send_troops = min(intermediate_send_troops, self.sendable_troops)                    
                    
                    destination.need_turn -= intermediate_send_troops
                    destination.need_turn = max(destination.need_turn, 0)
                    
                    self.sendable_troops -= intermediate_send_troops                    
                    send_troops += intermediate_send_troops
                    
                else: #XF
                    fact_destination.need_turn -= send_troops
                    fact_destination.need_turn = max(fact_destination.need_turn, 0)
                
                
                # print('get intermediate for ' + str(fact_destination.f_id), file=sys.stderr)                    
                #print('optimization ' + str(fact_destination.f_id) + ' becomes ' + str(destination.f_id), file=sys.stderr)                
                                                    
                print('TO: ' + str(fact_destination.f_id) + ', TI: ' + str(destination.f_id) + ' - P: ' + str(priority) + ' - D: ' + str(link.distance),
                      'N : ' + str(fact_destination.need_turn) + ' - S: ' + str(send_troops), file=sys.stderr)
    
                if send_troops != 0:
                    
                    self.orders.append(Order(Order.MOVE, self, destination, send_troops))    
                    factory_stock -= send_troops
                    #self.sendable_troops -= send_troops
    
                    #Decrease the need for the destination factory                
                    #destination.need_turn -= send_troops
                    #destination.need_turn = max(destination.need_turn, 0)
    
                    if self.sendable_troops == 0:
                        pass        

    def emit_excedent_orders(self):
        '''
        Send extra stock if the factory is with a production of 3 to other factory in danger
        '''
        
        if self.sendable_troops != 0 and self.production == 3:
            link_friend_factories = [link for link in self.links.values() if link.destination[self.f_id].owner == FRIEND]
            link_friend_factories.sort(key=lambda link: link.destination[self.f_id].index_danger, reverse=True)

            for link_friend in link_friend_factories:
                if self.sendable_troops > 0:
                    destination = link_friend_factories[0].destination[self.f_id]
                    if self.index_danger < destination.index_danger and destination.need_turn > 0:
                        
                        send_troops += max(min(destination.need_turn, self.sendable_troops - send_troops), 0)
                        
                        
                        send_troops = max(destination.need_turn, 1)
                        send_troops = min(send_troops, self.sendable_troops)
                        self.orders.append(Order(Order.MOVE, self, destination, self.send_troops))
    
                        self.sendable_troops -= send_troops
                        destination.need_turn -= send_troops
                        destination.need_turn = max(destination.need_turn, 0)
                else:
                    break
        
        if len(self.orders) == 0:
            self.orders.append(Order(Order.WAIT, self, self, 0))

    def get_intermediate(self, link, target):
        '''
        Return the closest intermediate from the factory to reach the target
        '''
        
        intermediate = target
        
        for key, link_int in self.links.items():
            candidate = link_int.destination[self.f_id]

            if candidate.f_id != target.f_id \
            and (candidate.owner == FRIEND or candidate.owner == NEUTRAL or candidate.owner == ENNEMY) \
            and (candidate.links[target.f_id].distance + candidate.links[self.f_id].distance + 1)  <= link.distance:                                
                if candidate.links[self.f_id].distance < intermediate.links[self.f_id].distance:
                    if intermediate.f_id == target.f_id:
                        intermediate = candidate
                    elif (candidate.links[target.f_id].distance + candidate.links[self.f_id].distance) <= (intermediate.links[target.f_id].distance + intermediate.links[self.f_id].distance):
                        intermediate = candidate
        
        return intermediate

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
        # R9 : promote yourself by blitzing reallu close ennemy
        '''

        priorities = simu.conquest_priorities
        selected_priorities = []

        present_destination = link.destination[self.f_id]
        simu_destination = simu.factories[present_destination.f_id]
        simu_self = simu.factories[self.f_id]
                
        if simu_destination.owner == ENNEMY and present_destination.owner == ENNEMY \
        and link.distance <= MAX_DISTANCE_CONSIDERED+1 \
        and (((link.distance - present_destination.bomb_eta) < 2 and (link.distance - present_destination.bomb_eta) >= 0 and present_destination.bomb_eta >= 0)):
        #or ((link.distance - present_destination.count_zero_prod) == 1 and present_destination.count_zero_prod > 0)):

            # R1 : attack your close opponent where he is bombed
            priority = priorities[0] * 1000
            priority += simu_destination.bomb_eta * 10
            priority += simu_destination.count_zero_prod * 10
            priority += simu_destination.production * 100
            priority += simu_destination.nb_ennemy_troops * 10
            priority += (20 - link.distance) * 10
            selected_priorities.append(priority)
            
        if simu_destination.owner == ENNEMY \
        and (simu_destination.stock + simu_destination.current_production + simu_destination.nb_friendly_troops) < simu_self.stock \
        and link.distance <= 1 and (simu_destination.production > simu_self.production or simu_self.production == 3):
            # R9 : promote yourself by blitzing really close ennemy
            
            priority = priorities[8] * 1000
            priority += simu_destination.production * 100
            priority -= simu_destination.stock
            priority -= simu_destination.min_ennemy_distance * 5
            priority += simu_destination.min_friend_distance * 5            
            selected_priorities.append(priority)
                    
        if simu_destination.owner == ENNEMY and present_destination.owner == FRIEND \
        and (link.distance - present_destination.bomb_eta) >= 0:
            
            # R2 : help your ex friends
            priority = priorities[1] * 1000
            priority += simu_destination.production * 10
            priority += 20 - link.distance
            selected_priorities.append(priority)
            
        if simu_destination.owner == FRIEND and (((simu_destination.stock + simu_destination.nb_friendly_troops + simu_destination.current_production) < simu_destination.nb_ennemy_troops)):  # or simu_destination.min_ennemy_distance == 1):
            # R3 : help your neighbor
            priority = priorities[2] * 1000
            priority += simu_destination.production
            priority += simu_destination.min_ennemy_distance
            selected_priorities.append(priority)

        if simu_destination.owner == FRIEND \
        and (self.production > simu_destination.production or self.bomb_eta >= 1) \
        and (simu_destination.bomb_eta <= 0) \
        and simu_destination.production <= 1 and simu_destination.nb_ennemy_troops == 0:
            # R4 : help your neighbor to increase production to level 2

            priority = priorities[3] * 1000
            
            #old config
            #priority += (1-simu_destination.production) * 100
            #priority += simu_destination.min_ennemy_distance
            
            #new_config - #Try to finish the closest one first to the next level of production first
            priority += simu_destination.production * 10
            priority += simu_destination.stock
            priority += simu_destination.nb_friendly_troops
            
            selected_priorities.append(priority)

        if simu_destination.owner == NEUTRAL:
            # R5 : expand around you on factories of interest

            priority = priorities[4] * 1000
            priority += simu_destination.production * 10
            priority += (20 - link.distance) * 7
            priority += simu_destination.min_ennemy_distance * 4
            priority -= simu_destination.min_friend_distance * 5
            priority -= simu_destination.stock
            priority -= simu_destination.nb_ennemy_troops * 10
            
            priority += int(simu_destination.is_central) * 50
            
            #close_other_factories = [link for key, link in simu_destination.links.items() if link.distance <= 2 and simu.factories[key].owner != FRIEND]
            #priority -= len(close_other_factories)
            
            selected_priorities.append(priority)

        if simu_destination.owner == ENNEMY and simu_destination.bomb_eta <= 0:
            # R6 : attack your close opponent where he is weak

            priority = priorities[5] * 1000
            priority += simu_destination.production * 10
            priority += (20 - link.distance) * 7
            priority -= simu_destination.min_ennemy_distance * 5
            priority += simu_destination.min_friend_distance * 5
            priority -= simu_destination.stock
            priority += simu_destination.nb_ennemy_troops * 10   
                                                            
            selected_priorities.append(priority)

        if simu_destination.owner == NEUTRAL:
            # R7 : expand:
            priority = priorities[6] * 1000
            priority += simu_destination.production * 10
            priority += simu_destination.min_ennemy_distance * 10
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
        self.central_factories = []
        
        self.original_owned = None
        self.original_ennemy= None

        self.links = []

        self.troops = []
        self.troops_owned = []
        self.troops_ennemy = []

        self.available_bomb = 2
        self.ennemy_available_bomb = 2

        self.delta_prod = 0
        self.prod_ennemy = 0
        self.prod_friend = 0
        self.turn_equality = 0
        
        self.nb_friend_troops = 0
        self.nb_ennemy_troops = 0

        self.mode = MODE_CONSOLIDATION
        self.conquest_priorities = [12, 11, 10, 9, 8, 7, 6, 5]

        self.turn = 1
        self.game_turn = 1

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

        self.nb_friend_troops = 0
        self.nb_ennemy_troops = 0

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
                    
                    temp_simu = self.clone()                    
                    for i in range(NB_SIMU_TURN):
                        temp_simu.simulate_turn()
                    
                    #factory_destination = self.estimate_target(factory_origin)
                    simu_factory_origin = temp_simu.factories[factory_origin.f_id]
                    simu_factory_destination = temp_simu.estimate_target(factory_origin, self)
                    factory_destination = self.factories[simu_factory_destination.f_id]
                    
                    link = factory_origin.links[factory_destination.f_id]
                    bomb_eta = link.distance
                    
                    self.ennemy_available_bomb -= 1
                    self.ennemy_available_bomb = max(self.ennemy_available_bomb, 0)
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

    def estimate_target(self, origin, game):
        '''
        Choose the possible target of the ennemy bomb and set the bomb eta accordingly
        '''
        
        if self.game_turn == 2: #Turn 1, orders are emitted so the target is decided on turn 2
            factories_except_origin = [factory for factory in game.factories_owned if factory.f_id != origin.f_id]
            
            target = factories_except_origin[0]
            eta = origin.links[target.f_id].distance - 1
        else:
            present_facto_bombed = [factory for factory in game.factories_owned if factory.bomb_eta >= origin.links[factory.f_id].distance]
            
            if len(present_facto_bombed) == 1:
                factories_except_origin = [factory for factory in self.factories_owned if factory.f_id != origin.f_id and factory.f_id != present_facto_bombed[0].f_id]
            else:
                factories_except_origin = [factory for factory in self.factories_owned if factory.f_id != origin.f_id]
                
            temp = sorted(factories_except_origin, key=lambda factory: (factory.bomb_eta, -factory.production, -factory.stock, factory.nb_ennemy_troops))
            target = temp[0]

        print('TARGET : ' + str(target.f_id), file=sys.stderr)

        return target

    def send_bomb_order(self, simulated_game):
        '''
        Manage to send a bomb if possible
        '''

        if self.available_bomb > 0:
            target = None
            sorted_factories = sorted(simulated_game.factories_ennemy, key=lambda factory: factory.production,reverse=True)
            
            max_ennemy_poduction = 0
            if len(simulated_game.factories_ennemy) > 0:
                max_ennemy_poduction = max(factory.production for factory in simulated_game.factories_ennemy)            
                
            max_friend_poduction = 0
            if len(simulated_game.factories_owned) > 0:
                max_friend_poduction = max(factory.production for factory in simulated_game.factories_owned)
            
            max_neutral_production = 0
            neutral_factories = [factory for factory in simulated_game.factories if factory.owner == NEUTRAL]
            if len(neutral_factories) > 0:
                max_neutral_production = max(factory.production for factory in neutral_factories)

            # TODO : improve bomb to send only if time in simu is less or equal than distance between friend factory and ennemy factory
            for factory in sorted_factories:

                # Improve bomb to not send to prod = 1 except if prod 1 is the max on all ennemies factories
                if (max_ennemy_poduction <= 1 and factory.production == 1 and factory.stock >= 0 and factory.bomb_eta <= 0 and factory.count_zero_prod <= 0) \
                or (max_ennemy_poduction >= 2 and factory.production >= 2 and factory.stock >= 0 and factory.bomb_eta <= 0 and factory.count_zero_prod <= 0):                    
                    
                    if (len(self.factories) <= MIN_NB_FACTORIES+2 and (self.turn >=2)) \
                    or (len(self.factories) > MIN_NB_FACTORIES and factory.production == max(max_ennemy_poduction, max_neutral_production)):                    
                        if target is None:
                            target = factory
                        elif factory.stock > target.stock and factory.min_ennemy_distance <= target.min_ennemy_distance :
                            target = factory

            if target is not None:
                sorted_links = sorted(target.links.values(), key=lambda link: link.distance)
                link_friend_factories = [link for link in sorted_links if link.destination[target.f_id].owner == FRIEND and link.distance > target.turn_change_owner]

                if len(link_friend_factories) != 0:
                    closest_friend_factory = link_friend_factories[0].destination[target.f_id]

                    # Test if the factory is already a friend, otherwise wait until it becomes a friend
                    if self.factories[closest_friend_factory.f_id].owner == FRIEND:
                        self.available_bomb -= 1
                        return Order(Order.BOMB, closest_friend_factory, target, 0)

        return None

    def send_orders_to_engine(self, simu):
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
        msg_prod +=  '    ' + simu.get_mode_str(True)
        filler = '                                                        '
        msg_prod += filler[0:len_field - len(msg_prod) - 12]
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

        for factory in self.factories:
            factory.set_distances()    

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
            
        if self.turn == 1:
            friend = self.factories_owned[0]
            ennemy = self.factories_ennemy[0]
            
            self.original_owned = friend
            self.original_ennemy= ennemy
            
            self.central_factories = [factory for factory in self.factories if factory.f_id != friend.f_id and factory.f_id != ennemy.f_id and factory.links[friend.f_id].distance == factory.links[ennemy.f_id].distance]
            for factory in self.central_factories:
                factory.is_central = True
            
    def get_mode_str(self, is_short = False):
        if self.mode == MODE_AGRESSIVE:
            if is_short:
                return 'AGRE'
            else:
                return 'Agressive'
        elif self.mode == MODE_CONQUERING:
            if is_short:
                return 'CONQ'
            else:
                return 'Conquering'
        else:
            if is_short:
                return 'CONS'
            else:
                return 'Consolidation'
                
    def solve_turn(self, simulated_game):

        print('GAME SOLVE TURN: ' + str(simulated_game.get_mode_str()), file=sys.stderr)
        message = ''
        
        for priority in simulated_game.conquest_priorities:
            message += ',' + str(priority)
        print('priorities : ' + message, file=sys.stderr)

        for factory in self.factories:
            factory.update_troops_after_moves()
            factory.update_need_for_turn(simulated_game)
            
        for factory in self.factories_owned:
            factory.compute_danger_index(simulated_game)
            factory.define_conquest_priorities(simu)
            factory.emit_orders(simulated_game)
        
        for factory in self.factories_owned:    
            factory.emit_excedent_orders()

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

        print(self.send_orders_to_engine(simulated_game))
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
        # R9 : blitz to improve production
        '''
        prod_ennemy = sum(factory.current_production for factory in self.factories_ennemy)
        prod_friend = sum(factory.current_production for factory in self.factories_owned)
        
        stock_ennemy = sum(factory.stock for factory in self.factories_ennemy)
        stock_friend = sum(factory.stock for factory in self.factories_owned)
        
        friend_cyborgs = [troop for troop in self.troops if troop.owner == FRIEND and not troop.is_bomb]
        ennemy_cyborgs = [troop for troop in self.troops if troop.owner == ENNEMY and not troop.is_bomb]
        
        self.nb_friend_troops = sum(cyborg.number for cyborg in friend_cyborgs)
        self.nb_ennemy_troops = sum(cyborg.number for cyborg in ennemy_cyborgs)
        
        neutral_factories = [factory for factory in self.factories if factory.owner == NEUTRAL]
        neutral_factories_0 = [factory for factory in self.factories if factory.owner == NEUTRAL and factory.production == 0]
        
        nb_fact_friend_max_prod = len([factory for factory in self.factories if factory.owner == FRIEND and factory.production == 3])
        nb_close_neutral_prod = len([factory for factory in self.factories if factory.owner == NEUTRAL and factory.production > 0 and factory.min_friend_distance <= MAX_DISTANCE_CONSIDERED+1])
        nb_central_neutral = len([factory for factory in self.central_factories if factory.owner == NEUTRAL])                         
                                                
        if len(neutral_factories) > 0:
            ratio_0_production = len(neutral_factories_0)/len(neutral_factories)
        else:
            ratio_0_production = 0.0
                
        print('prod f.: ' + str(prod_friend) + ', prod e: ' + str(prod_ennemy) +', diff nb facto:' + str(len(self.factories_owned) <= len(self.factories_ennemy)) + ', ratio0: ' + str(round(ratio_0_production,2)) + ', close: ' + str(nb_close_neutral_prod) + ', central : ' + str(nb_central_neutral), file=sys.stderr) 
        
        if ((len(self.factories) <= MIN_NB_FACTORIES and stock_ennemy - stock_friend <= 5 and self.original_owned.min_ennemy_distance <= 10) \
        or (self.original_owned.links[self.original_ennemy.f_id].distance <= MAX_DISTANCE_CONSIDERED and ratio_0_production > 0.9))\
        and prod_friend >= prod_ennemy:
        #and prod_friend - prod_ennemy <= 1:
            self.mode = MODE_AGRESSIVE
            self.conquest_priorities = [12, 11, 10, 7, 8, 9, 5, 6, 13]
        elif (prod_friend - prod_ennemy) <= 1 and len(neutral_factories) > 0 and (ratio_0_production <= 0.35 or nb_close_neutral_prod > 0 or nb_central_neutral > 0):
        #elif (prod_friend - prod_ennemy) >= -1 and (prod_friend - prod_ennemy) <= 1 and len(neutral_factories) > 0 and (ratio_0_production <= 0.35 or nb_close_neutral_prod > 0 or nb_central_neutral > 0):
            self.mode = MODE_CONQUERING
            self.conquest_priorities = [12, 11, 10, 0, 9, 8, 7, 5, 13]            
            #self.conquest_priorities = [12, 11, 10, 9, 9, 6, 7, 5, 13]            
        elif (prod_friend - prod_ennemy) <= 6 and len(self.factories) >= MIN_NB_FACTORIES and len(self.factories_owned) >= nb_fact_friend_max_prod:
            self.mode = MODE_CONSOLIDATION
            #self.conquest_priorities = [12, 11, 10, 9, 9, 7, 6, 5]
            self.conquest_priorities = [12, 11, 10, 9, 8, 8, 6, 5, 13]
        else:
            self.mode = MODE_AGRESSIVE
            self.conquest_priorities = [12, 11, 10, 7, 8, 9, 5, 6, 13]

    def clone(self):
        clone = Game()

        for factory in game.factories:
            clone_factory = factory.clone_basic_attributes()
            clone.factories.append(clone_factory)

            if clone_factory.owner == FRIEND:
                clone.factories_owned.append(clone_factory)
            elif clone_factory.owner == ENNEMY:
                clone.factories_ennemy.append(clone_factory)        

            is_central = [factory for factory in self.central_factories if factory.f_id == clone_factory.f_id]
            if len(is_central) > 0:
                clone.central_factories.append(clone_factory)
                
        clone.original_owned = clone.factories[self.original_owned.f_id]
        clone.original_ennemy = clone.factories[self.original_ennemy.f_id]

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
        clone.ennemy_available_bomb = self.ennemy_available_bomb
        
        clone.delta_prod = self.delta_prod
        clone.prod_ennemy = self.prod_ennemy
        clone.prod_friend = self.prod_friend
        clone.turn_equality = self.turn_equality

        clone.nb_friend_troops = self.nb_friend_troops
        clone.nb_ennemy_troops = self.nb_ennemy_troops
        clone.mode = self.mode
        
        clone.turn = 0  # self.turn
        clone.game_turn = self.turn

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
    start_time = time.time()
    
    game.reset()
    
    list_input = []
    entity_count = int(input())  # the number of entities (e.g. factories and troops)
    for i in range(entity_count):
        entity_id, entity_type, arg_1, arg_2, arg_3, arg_4, arg_5 = input().split()
        entity_id = int(entity_id)
        arg_1 = int(arg_1)
        arg_2 = int(arg_2)
        arg_3 = int(arg_3)
        arg_4 = int(arg_4)
        arg_5 = int(arg_5)
        
        list_input.append(Input(entity_type, entity_id, arg_1, arg_2, arg_3, arg_4, arg_5))
    
    list_input.sort(key=attrgetter('entity_type'), reverse=True) #Sort them by type (bomb last)    
    for new_input in list_input:        
        game.process_input(new_input.entity_id, new_input.entity_type, new_input.arg1, new_input.arg2, new_input.arg3, new_input.arg4, new_input.arg5)

    game.consolidate_inputs()

    game.set_game_mode()
    
    simu = game.clone()

    MAX_DISTANCE_CONSIDERED = max(game.get_min_distance_in_level(), MAX_DISTANCE_CONSIDERED)
    NB_SIMU_TURN = MAX_DISTANCE_CONSIDERED + 1

    for i in range(NB_SIMU_TURN):
        simu.simulate_turn()

    simu.set_game_mode()
    game.solve_turn(simu)
    
    elapsed_time = (time.time() - start_time) * 1000.0 # ms
    print('ELAPSED TIME = ' + str(elapsed_time),file=sys.stderr)