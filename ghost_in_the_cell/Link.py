from Game import Game
from Troop import Troop
from Configuration import *



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


    def add_troops(self, origin, destination, number, is_bomb):
        '''
        Create and add new troops on the link
        :param origin: factory creating the troops
        :param destination: factory destination of the troops
        :param number: number of the troops
        :param is_bomb: the troop is a bomb
        '''

        troop = Troop(1000, number, self.distance, origin.owner, is_bomb, self, origin, destination)
        self.troops[destination.f_id].append(troop)
