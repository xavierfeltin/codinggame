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