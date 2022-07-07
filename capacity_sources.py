from simpy import FilterStore, PriorityResource


class Machine(PriorityResource):
    def __init__(self,
                 sim,
                 env,
                 capacity_slots,
                 id
                 ) -> None:
        super().__init__(env=env, capacity=capacity_slots)
        self.sim = sim
        self.capacity_slots = capacity_slots
        self.identifier = id
        self.name = f'Machine {self.identifier}'
        return

    def __str__(self):
        return self.name


class Queue(FilterStore):
    def __init__(self,
                 sim,
                 env,
                 id
                 ) -> None:
        super().__init__(env=env)
        self.sim = sim
        self.identifier = id
        self.name = f'Queue {self.identifier}'
        return

    def __str__(self):
        return self.name


class Pool(FilterStore):
    def __init__(self,
                 sim,
                 env,
                 id
                 ) -> None:
        super().__init__(env=env)
        self.sim = sim
        self.identifier = id
        self.name = f'Pool {self.identifier}'
        return

    def __str__(self):
        return self.name


class Inventory(FilterStore):
    def __init__(self,
                 sim,
                 env,
                 id
                 ) -> None:
        super().__init__(env=env)
        self.sim = sim
        self.identifier = id
        self.name = f'Inventory {self.identifier}'
        return

    def __str__(self):
        return self.name
