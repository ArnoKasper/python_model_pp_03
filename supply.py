from random import Random


class Supply(object):
    def __init__(self, simulation):
        self.sim = simulation
        self.random_generator: Random = Random()
        self.random_generator.seed(999999)
        return

    def delivery(self):
        """
        1.) find delivery time
        2.) timeout until delivery
        3.) create material, put in inventory
        """
        return