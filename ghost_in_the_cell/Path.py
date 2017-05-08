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
