from operator import itemgetter
from random import Random
from flowitem import Order
import math

class Generation(object):
    def __init__(self, simulation):
        """
        :param simulation:
        :param stationary:
        """
        self.sim = simulation
        self.random_generator = Random()
        self.random_generator.seed(999999)

        # key params
        self.i = 1
        self.mean_time_between_arrivals = self.sim.model_panel.MEAN_TIME_BETWEEN_ARRIVAL
        self.generation_technique = self.sim.policy_panel.generation_technique.copy()
        self.generation_attributes = self.sim.policy_panel.generation_attributes

        # forecast
        self.forecast_technique = {}
        self.forecast_attributes = {}

        # item structure
        self.items = self.sim.model_panel.items
        self.BOM = self.sim.model_panel.BOM
        self.dependencies = self.sim.model_panel.dependencies
        return

    def initialize_generation(self):
        for item, generation_attr in reversed(self.generation_technique.items()):
            if generation_attr['technique'] == "constant":
                # constant arrivals
                self.sim.generation_process[item] = self.sim.env.process(
                    self.generate_random_arrival_exp(item=item, type='constant', line=generation_attr['line']))
            elif generation_attr['technique'] == "exponential":
                # Markovian arrivals
                self.sim.generation_process[item] = self.sim.env.process(
                    self.generate_random_arrival_exp(item=item, type='exponential', line=generation_attr['line']))
            elif generation_attr['technique'] == 'control_loop':
                # generation via control loop
                self.sim.generation_process[item] = "control_loop"
                while True:
                    # make an order
                    generated = self.generate_control_loop(item=item, warmup=True)
                    if not generated:
                        # no more new generations
                        break
            elif generation_attr['technique'] == "MRP":
                # activate forecasting
                self.forecast_technique[item] = "MRP_forecast"
                self.forecast_attributes[item] = FORECAST_TECHNIQUE_ATTRIBUTES['MRP_forecast']
                # activate MRP
                self.sim.generation_process[item] = self.sim.env.process(self.material_requirements_planning(item=item))
            elif generation_attr['technique'] == "dynamic_coupling":
                self.sim.generation_process[item] = "dynamic_coupling"
                # create uncoupled safety material
                while True:
                    # make an order
                    generated = self.sim.dynamic_coupling.generate_uncoupled_safety_material(item=item)
                    if not generated:
                        # no more new generations
                        break
            else:
                raise Exception(f"generation process {self.generation_technique} is not known")

    def generate_random_arrival_exp(self, item, type, line):
        while True:
            # generate
            self.generate_and_put_in_pool(item=item)
            # find next arrival time
            if type == 'exponential':
                inter_arrival_time = self.sim.random_generator.expovariate(1 / self.mean_time_between_arrivals[line])
            elif type == 'constant':
                inter_arrival_time = self.mean_time_between_arrivals[line]
            else:
                raise Exception(f"generation type is unknown")

            yield self.sim.env.timeout(inter_arrival_time)
            self.i += 1
            if self.sim.env.now >= (self.sim.model_panel.WARM_UP_PERIOD + self.sim.model_panel.RUN_TIME) \
                    * self.sim.model_panel.NUMBER_OF_RUNS:
                break

    def generate_control_loop(self, item, warmup=False):
        if self.sim.generation_process[item] == 'control_loop':
            inventory_level = len(self.sim.model_panel.SKU[item].items)
            in_process = self.generation_attributes[item]['generated'] - self.generation_attributes[item]['delivered']
            # control if loop allows new generation
            if (inventory_level + in_process) < self.generation_attributes[item]['generation_target']:
                # generate
                if not warmup:
                    self.generate_and_put_in_pool(item=item)
                else:
                    self.generate_and_put_in_inventory(item=item)
                # add
                self.generation_attributes[item]['generated'] += 1
                # generation
                generation = True
            else:
                # no new order is generated
                generation = False
        else:
            # no valid generator
            generation = False
        return generation

    def material_requirements_planning(self, item):
        # initialize params
        safety_stock = self.generation_attributes[item]['safety_stock']
        horizon = self.generation_attributes[item]['horizon']
        safety_lead_time = self.generation_attributes[item]['safety_lead_time']
        lead_time = self.generation_attributes[item]['lead_time']
        planned_lead_time = int(math.ceil((lead_time + safety_lead_time) / horizon))
        quantity = self.generation_attributes[item]['quantity']
        lot_sizing_rule = self.generation_attributes[item]['lot_sizing_rule']

        # update list for first run
        self.generation_attributes[item]['scheduled_receipts'] = [0] * horizon
        self.forecast_attributes[item]['demand_forecast'] = [
            self.forecast_attributes[item]['end_item_forecasted_demand']
        ] * horizon

        # loop to determine periodically the material requirements
        while True:
            # update demand
            self.demand_forecast(item=item)

            # initialize params
            D = self.forecast_attributes[item]['demand_forecast']
            S = self.generation_attributes[item]['scheduled_receipts']
            I = len(self.sim.model_panel.SKU[item].items)
            I_t_minus_1 = I - safety_stock
            planned_receipts = [0] * horizon
            planned_release = [0] * horizon

            # schedule material requirements
            for t in range(0, horizon):
                # increase demand if safety stock is too little
                if I_t_minus_1 < 0:
                    D[t] += abs(I_t_minus_1)
                    I_t_minus_1 = 0
                # compute projected available
                I_t = I_t_minus_1 + S[t] - D[t]
                N_t = min(max(-1 * I_t, 0), D[t])
                # determine lot size
                if lot_sizing_rule == 'lot_for_lot':
                    lots_needed = int(math.ceil((abs(N_t)) / quantity))
                    planned_receipts[t] = abs(lots_needed * quantity)
                else:
                    raise Exception(f'lot sizing rule: {lot_sizing_rule} unknown')
                # update for t + 1
                I_t_minus_1 = planned_receipts[t] - N_t

            # schedule planned releases
            for t in reversed(range(0, horizon)):
                if t - planned_lead_time > 0:
                    planned_release[t - planned_lead_time] = planned_receipts[t]
                else:
                    # planned order past due, assume earliest still possible release time
                    planned_release[0] += planned_receipts[t]

            # determine scheduled receipts for next period and the planned releases
            self.generation_attributes[item]['scheduled_receipts'][0] = planned_release[0]
            self.generation_attributes[item]['planned_release'] = planned_release

            # generate
            for i in range(0, planned_release[0]):
                # generate i items
                self.generate_and_put_in_pool(item=item)

            # wait until the next time bucket
            yield self.sim.env.timeout(self.generation_attributes[item]['bucket_size'])
            # new period, recompute

    def generate_and_put_in_pool(self, item):
        # generate new order: create an order object and give it a name
        order = Order(simulation=self.sim,
                      identifier=self.identifier(),
                      attributes=self.sim.model_panel.BOM[item])
        # send order to process
        self.sim.release.put_in_pool(order=order, line=order.line)
        return

    def generate_and_put_in_inventory(self, item):
        # generate new order: create an order object and give it a name
        order = Order(simulation=self.sim,
                      identifier=self.identifier(),
                      attributes=self.sim.model_panel.BOM[item])
        # send order to process
        self.sim.inventory.put_in_inventory(order=order)
        return

    def check_generation(self, item):
        generation = True
        if self.sim.generation_process[item] == 'control_loop':
            # subtract
            self.generation_attributes[item]['delivered'] += 1
            # control if new generation is possible
            generation = self.generate_control_loop(item=item)
        elif self.sim.generation_process[item] == 'dynamic_coupling':
            # decouple
            self.sim.dynamic_coupling.coupled(item=item)
            # control if new generation is possible
            generation = self.sim.dynamic_coupling.generate_uncoupled_safety_material(item=item)
        return generation

    def identifier(self):
        i = self.i
        self.i += 1
        return i

    def demand_forecast(self, item):
        # make forecasts
        if self.sim.model_panel.BOM[item]['material_type'] == "end":
            # remove old period
            self.forecast_attributes[item]['demand_forecast'].pop(0)
            # add new forecasted demand
            self.forecast_attributes[item]['demand_forecast'].append(
                self.forecast_attributes[item]['end_item_forecasted_demand']
            )
        elif self.sim.model_panel.BOM[item]['material_type'] == "component":
            # get derived demand
            demand = []
            planned_release = []
            demand_sources = self.dependencies[item]
            for demand_source in demand_sources:
                planned_release.append(self.generation_attributes[demand_source]['planned_release'])
            # bom explosion
            for t in range(0, self.generation_attributes[item]['horizon']):
                quantity = 1
                demand_t = 0
                # collect all demand from all sources
                for planned_release_i in planned_release:
                    demand_t += planned_release_i[t]
                demand.append(demand_t * quantity)
            self.forecast_attributes[item]['demand_forecast'] = demand
        return


FORECAST_TECHNIQUE_ATTRIBUTES = {
    'MRP_forecast': {'technique': 'constant',
                     'demand_forecast': [],
                     'end_item_forecasted_demand': 1
                    },
}
