import Game
from Configuration import *
import Factory

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