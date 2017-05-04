import unittest
from Factory import Factory
from Troop import Troop
from Link import Link
from Order import Order
from Configuration import *

class TestLink(unittest.TestCase):
    def set_up(self):
        '''
        Fact 1 = player , stock 5, prod 2, sent troops to Fact 2 (ETA = 1)
        Fact 2 = neutral , stock 3
        Fact 3 = ennemy, stock 5, prod 2, sent troops to Fact 2 (ETA = 1)

        Fact 1 - Fact 2 = distance 3
        Fact 3 - Fact 2 = distance 3
        Fact 1 - Fact 3 = distance 7
        '''
        self.fact_1 = Factory(0)
        self.fact_2 = Factory(1)
        self.fact_3 = Factory(2)

        self.link_1_3 = Link(0, self.fact_1, self.fact_3, 7)
        self.link_1_2 = Link(1, self.fact_1, self.fact_2, 3)
        self.link_3_2 = Link(2, self.fact_3, self.fact_2, 3)

        self.troop_1 = Troop(0, 2, 0, FRIEND, False, self.link_1_2, self.fact_1, self.fact_2)
        self.troop_3 = Troop(2, 2, 0, FRIEND, False, self.link_1_2, self.fact_1, self.fact_2)
        self.troop_5 = Troop(4, 2, 1, FRIEND, False, self.link_1_2, self.fact_1, self.fact_2)

        self.troop_2 = Troop(1, 1, 0, ENNEMY, False, self.link_3_2, self.fact_3, self.fact_2)
        self.troop_4 = Troop(3, 2, 0, ENNEMY, False, self.link_3_2, self.fact_3, self.fact_2)
        self.troop_6 = Troop(5, 2, 1, ENNEMY, False, self.link_3_2, self.fact_3, self.fact_2)

        self.troop_7 = Troop(6, 2, 0, ENNEMY, False, self.link_1_3, self.fact_3, self.fact_1)
        self.troop_8 = Troop(6, 1, 0, FRIEND, False, self.link_1_3, self.fact_1, self.fact_3)

        self.set_fact(self.fact_1, 5, 2, FRIEND, [self.link_1_3, self.link_1_2])
        self.set_fact(self.fact_3, 5, 2, ENNEMY, [self.link_1_3, self.link_3_2])
        self.set_fact(self.fact_2, 3, 1, 0, [self.link_1_2, self.link_3_2])

        self.set_distance(self.fact_1)
        self.set_distance(self.fact_2)
        self.set_distance(self.fact_3)

        self.set_troops([self.troop_1, self.troop_2, self.troop_3, self.troop_4, self.troop_5, self.troop_6, self.troop_7, self.troop_8])

    def set_fact(self, fact, stock, prod, owner, links):
        fact.stock = stock
        fact.production = prod
        fact.current_production = prod
        fact.owner = owner

        for link in links:
            fact.links[link.destination[fact.f_id].f_id] = link

        fact.alternative_pathes = {}

    def set_distance(self, fact):
        fact.set_distances()
        #fact.initialize_nb_cyborgs_coming()

    def set_troops(self, troops):
        for troop in troops:
            troop.origin.sent_troops(troop.destination.f_id, troop)
            #troop.destination.add_coming_cyborgs(troop)

    def test_compute_friendly_troops_neutral_factory(self):
        self.set_up()
        nb_troops = self.link_1_2.get_friendly_troops_for_battle(self.fact_2)
        self.assertEqual(nb_troops,4)

    def test_compute_friendly_troops_friend_factory(self):
        self.set_up()
        nb_troops = self.link_1_2.get_friendly_troops_for_battle(self.fact_1)
        self.assertEqual(nb_troops, 0)

    def test_compute_friendly_troops_ennemy_factory(self):
        self.set_up()
        nb_troops = self.link_1_3.get_friendly_troops_for_battle(self.fact_3)
        self.assertEqual(nb_troops, 0)

    def test_compute_enemy_troops_neutral_factory(self):
        self.set_up()
        nb_troops = self.link_3_2.get_ennemy_troops_for_battle(self.fact_2)
        self.assertEqual(nb_troops, 3)

    def test_compute_enemy_troops_friend_factory(self):
        self.set_up()
        nb_troops = self.link_1_3.get_ennemy_troops_for_battle(self.fact_1)
        self.assertEqual(nb_troops, 2)

    def test_compute_enemy_troops_ennemy_factory(self):
        self.set_up()
        nb_troops = self.link_1_3.get_ennemy_troops_for_battle(self.fact_3)
        self.assertEqual(nb_troops, 1)

    def test_move_troops(self):
        self.set_up()
        self.link_1_2.move_troops()

        self.assertEqual(len(self.link_1_2.troops[self.fact_2.f_id]), 1)
        self.assertEqual(self.link_1_2.troops[self.fact_2.f_id][0].eta, 0)