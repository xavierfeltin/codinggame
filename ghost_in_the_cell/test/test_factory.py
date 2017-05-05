import unittest
from Factory import Factory
from Troop import Troop
from Link import Link
from Order import Order
from Configuration import *
from Game import Game

class TestFactory(unittest.TestCase):

    def set_up(self):
        '''
        Fact 1 = player , stock 5, prod 2, sent troops to Fact 2 (ETA = 1)
        Fact 2 = neutral , stock 3
        Fact 3 = ennemy, stock 5, prod 2, sent troops to Fact 2 (ETA = 1)

        Fact 1 - Fact 2 = distance 3
        Fact 3 - Fact 2 = distance 3
        Fact 1 - Fact 3 = distance 7
        '''

        self.game = Game()

        self.fact_1 = Factory(0)
        self.fact_2 = Factory(1)
        self.fact_3 = Factory(2)

        self.link_1_3 = Link(0, self.fact_1, self.fact_3, 7)
        self.link_1_2 = Link(1, self.fact_1, self.fact_2, 3)
        self.link_3_2 = Link(2, self.fact_3, self.fact_2, 3)

        self.troop_1 = Troop(0, 2, 0, FRIEND, False, self.link_1_2, self.fact_1, self.fact_2)
        self.troop_2 = Troop(1, 1, 0, ENNEMY, False, self.link_3_2, self.fact_3, self.fact_2)

        self.set_fact(self.fact_1, 5, 2, FRIEND, [self.link_1_3, self.link_1_2])
        self.set_fact(self.fact_3, 5, 2, ENNEMY, [self.link_1_3, self.link_3_2])
        self.set_fact(self.fact_2, 3, 1, 0, [self.link_1_2, self.link_3_2])

        self.set_distance(self.fact_1)
        self.set_distance(self.fact_2)
        self.set_distance(self.fact_3)

        self.set_troops([self.troop_1, self.troop_2])

        self.fact_1.update_troops_after_moves()
        self.fact_2.update_troops_after_moves()
        self.fact_3.update_troops_after_moves()

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
            self.game.real.troops.append(troop)

    def test_valid_set_distances_troops(self):
        self.set_up()
        self.assertEqual(self.fact_1.max_distance, 7)
        self.assertEqual(self.fact_1.min_distance, 3)
        self.assertEqual(self.fact_1.max_friend_distance, 0)
        self.assertEqual(self.fact_1.min_friend_distance, 20)
        self.assertEqual(self.fact_1.max_ennemy_distance, 7)
        self.assertEqual(self.fact_1.min_ennemy_distance, 7)

        self.assertEqual(self.fact_2.nb_friendly_troops, 2)
        self.assertEqual(self.fact_2.nb_ennemy_troops, 1)

    def test_solve_turn_neutral_factory_remains_neutral(self):
        self.set_up()

        self.fact_2.update_troops_after_moves()
        self.fact_2.execute_orders()
        self.fact_2.solve_battle()

        self.assertEqual(self.fact_2.owner, 0)
        self.assertEqual(self.fact_2.stock, 0)

    def test_solve_turn_neutral_factory_become_friendly(self):
        self.set_up()
        troop = Troop(10, 1, 0, 1, False, self.link_1_2, self.fact_1, self.fact_2)
        self.set_troops([troop])

        self.fact_2.update_troops_after_moves()
        self.fact_2.execute_orders()
        self.fact_2.solve_battle()

        self.assertEqual(self.fact_2.owner, FRIEND)
        self.assertEqual(self.fact_2.stock, 1)

    def test_solve_turn_neutral_factory_become_ennemy(self):
        self.set_up()
        troop = Troop(10, 2, 0, -1, False, self.link_3_2, self.fact_3, self.fact_2)
        self.set_troops([troop])

        self.fact_2.update_troops_after_moves()
        self.fact_2.execute_orders()
        self.fact_2.solve_battle()

        self.assertEqual(self.fact_2.owner, ENNEMY)
        self.assertEqual(self.fact_2.stock, 2)

    def test_solve_turn_friend_factory_send_troops(self):
        self.set_up()
        self.fact_1.orders.append(Order(Order.MOVE, self.fact_1, self.fact_2, 3))

        self.fact_1.update_troops_after_moves()
        self.fact_1.execute_orders()
        self.fact_1.solve_battle()

        self.assertEqual(self.fact_1.owner, FRIEND)
        self.assertEqual(self.fact_1.stock, 4)
        self.assertEqual(self.fact_1.current_production, self.fact_1.production)

    def test_solve_turn_friend_factory_increase_production(self):
        self.set_up()
        self.fact_1.stock = 13
        self.fact_1.orders.append(Order(Order.INC, self.fact_1, None, 10))

        self.fact_1.update_troops_after_moves()
        self.fact_1.execute_orders()
        self.fact_1.solve_battle()

        self.assertEqual(self.fact_1.owner, FRIEND)
        self.assertEqual(self.fact_1.stock, 6)
        self.assertEqual(self.fact_1.production, 3)
        self.assertEqual(self.fact_1.current_production, self.fact_1.production)

    def test_solve_turn_friend_attacked_stay_friend(self):
        self.set_up()
        self.fact_1.orders.append(Order(Order.MOVE, self.fact_1, self.fact_2, 4))
        troop = Troop(10, 1, 0, -1, False, self.link_1_3, self.fact_3, self.fact_1)
        self.set_troops([troop])
        self.fact_1.update_troops_after_moves()
        self.fact_1.execute_orders()
        self.fact_1.solve_battle()

        self.assertEqual(self.fact_1.owner, FRIEND)
        self.assertEqual(self.fact_1.stock, 2)
        self.assertEqual(self.fact_1.current_production, self.fact_1.production)

    def test_solve_turn_friend_attacked_become_ennemy(self):
        self.set_up()
        self.fact_1.orders.append(Order(Order.MOVE, self.fact_1, self.fact_2, 4))
        troop = Troop(10, 4, 0, -1, False, self.link_3_2, self.fact_3, self.fact_1)
        self.set_troops([troop])
        self.fact_1.update_troops_after_moves()
        self.fact_1.execute_orders()
        self.fact_1.solve_battle()

        self.assertEqual(self.fact_1.owner, ENNEMY)
        self.assertEqual(self.fact_1.stock, 1)
        self.assertEqual(self.fact_1.current_production, self.fact_1.production)

    def test_solve_turn_friend_attacked_stay_friend_helped(self):
        self.set_up()

        self.fact_1.orders.append(Order(Order.MOVE, self.fact_1, self.fact_2, 4))
        troop1 = Troop(10, 4, 0, -1, False, self.link_3_2, self.fact_3, self.fact_1)

        # TODO : add a friend factory instead of using ennemy factory for test
        troop2 = Troop(11, 2, 0, 1, False, self.link_3_2, self.fact_3, self.fact_1)
        self.set_troops([troop1, troop2])

        self.fact_1.update_troops_after_moves()
        self.fact_1.execute_orders()
        self.fact_1.solve_battle()

        self.assertEqual(self.fact_1.owner, FRIEND)
        self.assertEqual(self.fact_1.stock, 1)
        self.assertEqual(self.fact_1.current_production, self.fact_1.production)

    def test_solve_turn_friend_bombed_attacked_become_ennemy(self):
        self.set_up()
        self.fact_1.current_production = 0
        self.fact_1.count_zero_prod = 3
        self.fact_1.orders.append(Order(Order.MOVE, self.fact_1, self.fact_2, 4))
        troop = Troop(10, 2, 0, -1, False, self.link_3_2, self.fact_3, self.fact_1)
        self.set_troops([troop])
        self.fact_1.solve_turn()

        self.assertEqual(self.fact_1.owner, ENNEMY)
        self.assertEqual(self.fact_1.stock, 1)
        self.assertEqual(self.fact_1.current_production, 0)
        self.assertEqual(self.fact_1.production, 2)
        self.assertEqual(self.fact_1.count_zero_prod, 2)

    def test_solve_turn_friend_increased_attacked_stay_friend(self):
        self.set_up()
        self.fact_1.stock = 13
        self.fact_1.orders.append(Order(Order.INC, self.fact_1, self.fact_2, 10))
        self.fact_1.orders.append(Order(Order.MOVE, self.fact_1, self.fact_2, 3))
        troop = Troop(10, 2, 0, -1, False, self.link_1_3, self.fact_3, self.fact_1)
        self.set_troops([troop])

        self.fact_1.update_troops_after_moves()
        self.fact_1.execute_orders()
        self.fact_1.solve_battle()

        self.assertEqual(self.fact_1.owner, FRIEND)
        self.assertEqual(self.fact_1.stock, 1)
        self.assertEqual(self.fact_1.current_production, 3)
        self.assertEqual(self.fact_1.production, 3)
        self.assertEqual(self.fact_1.count_zero_prod, 0)

    def test_solve_turn_friend_increased_bombed_attacked_become_ennemy(self):
        self.set_up()
        self.fact_1.stock = 13
        self.fact_1.current_production = 0
        self.fact_1.count_zero_prod = 3
        self.fact_1.orders.append(Order(Order.INC, self.fact_1, self.fact_2, 10))
        self.fact_1.orders.append(Order(Order.MOVE, self.fact_1, self.fact_2, 3))
        #self.fact_1.cyborgs_coming[ENNEMY][0] = 2
        troop = Troop(10, 2, 0, -1, False, self.link_3_2, self.fact_3, self.fact_1)
        self.set_troops([troop])
        self.fact_1.solve_turn()

        self.assertEqual(self.fact_1.owner, ENNEMY)
        self.assertEqual(self.fact_1.stock, 2)
        self.assertEqual(self.fact_1.current_production, 0)
        self.assertEqual(self.fact_1.production, 3)
        self.assertEqual(self.fact_1.count_zero_prod, 2)

    def test_compute_troops_on_neutral(self):
        self.set_up()
        nb_troops = self.fact_1.compute_troops_to_send(self.fact_2)
        self.assertEqual(nb_troops, 3)

    def test_compute_troops_on_ennemy(self):
        self.set_up()
        nb_troops = self.fact_1.compute_troops_to_send(self.fact_3)
        self.assertEqual(nb_troops, 8)

    def test_compute_troops_on_bombed_ennemy(self):
        self.set_up()
        self.fact_3.count_zero_prod = 3
        nb_troops = self.fact_1.compute_troops_to_send(self.fact_3)
        self.assertEqual(nb_troops, 6)

    def test_compute_troops_on_ennemy_with_friends(self):
        self.set_up()
        self.fact_3.nb_ennemy_troops = 8
        nb_troops = self.fact_1.compute_troops_to_send(self.fact_3)
        self.assertEqual(nb_troops, 0)

    def test_execute_order_inc(self):
        self.set_up()
        self.fact_1.stock = 12
        self.fact_1.orders.append(Order(Order.INC, self.fact_1, self.fact_1, 10))
        self.fact_1.execute_orders()

        self.assertEqual(self.fact_1.production, 3)
        self.assertEqual(self.fact_1.stock, 2)

    def test_execute_order_move(self):
        self.set_up()
        self.fact_1.orders.append(Order(Order.MOVE, self.fact_1, self.fact_3, 2))
        self.fact_1.execute_orders()

        self.assertEqual(self.fact_1.stock, 3)
        self.assertEqual(len(self.link_1_3.troops[self.fact_3.f_id]), 1)
        self.assertEqual(self.link_1_3.get_ennemy_troops_for_battle(self.fact_3), 0)

if __name__ == '__main__':
    unittest.main()