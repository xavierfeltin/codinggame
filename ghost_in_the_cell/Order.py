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