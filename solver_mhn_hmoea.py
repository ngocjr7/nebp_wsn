from geneticpython.engines import NSGAIIEngine
from geneticpython import Population
from geneticpython.core.operators import TournamentSelection
from geneticpython.tools import visualize_fronts, save_history_as_gif
from geneticpython.models.tree import EdgeSets, KruskalTree
from geneticpython.core.operators import PrimCrossover, SwapMutation, OrderCrossover
from geneticpython.utils import check_random_state

from edge_sets import HMOEAEncoder, HMOEAEngine
from initalization import initialize_pop
from utils.configurations import *
from utils import WusnInput, energy_consumption
from utils import save_results
from problems import MultiHopProblem
from rooted_networks import MultiHopNetwork
from networks import WusnKruskalNetwork

from random import Random
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt
import random
import json
import copy
import time
import yaml

import sys
import os

WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(WORKING_DIR, './configs/_configurations.yml')

def check_config(config, filename, model):
    if config['data']['name'] not in filename:
        raise ValueError('Model {} is used for {}, file {} is not'.format(model, config['data'], filename))
    if config['encoding']['name'] != 'hmoea':
        raise ValueError('encoding {} != {}'.format(config['encoding']['name'], 'mprim3'))
    if config['algorithm']['name'] != 'nsgaii':
        raise ValueError('algorithm {} != {}'.format(config['algorithm']['name'], 'nsgaii'))

def solve(filename, output_dir=None, model='0.0.0.0', config=None, save_history=True, seed=None, save=True):
    start_time = time.time()

    seed = seed or 42
    config = config or {}
    config = update_config(load_config(CONFIG_FILE, model), config)
    check_config(config, filename, model)
    output_dir = output_dir or gen_output_dir(filename, model)
    basename, _ = os.path.splitext(os.path.basename(filename))
    os.makedirs(os.path.join(
        WORKING_DIR, '{}/{}'.format(output_dir, basename)), exist_ok=True)

    wusnfile = os.path.join(WORKING_DIR, filename)
    inp = WusnInput.from_file(wusnfile)
    update_max_hop(config, inp)
    update_gens(config, inp)
    print(basename, config)
    problem = MultiHopProblem(inp, config['data']['max_hop'])
    network = MultiHopNetwork(problem)
    node_count = problem._num_of_relays + problem._num_of_sensors + 1
    edge_count = problem._num_of_sensors
    adj = copy.deepcopy(problem.weighted_adj)
    for i in range(len(adj)):
        adj[i].sort()

    indv_temp = HMOEAEncoder(max_hop=config['data']['max_hop'],
                             num_sensors=problem._num_of_sensors,
                             num_relays=problem._num_of_relays,
                             solution=network,
                             adj=adj)

    population = Population(indv_temp, 20)

    @population.register_initialization
    def init_population(random_state=None):
        return initialize_pop(config['encoding']['init_method'],
                              network=network, 
                              problem=problem,
                              indv_temp=indv_temp, 
                              size=population.size,
                              max_hop=problem.max_hop,
                              random_state=random_state)

    mutation = SwapMutation(pm=0.4)
    crossover = OrderCrossover(pc=0.6)
    selection = TournamentSelection(3)


    engine = HMOEAEngine(min_relays=1,
                         max_relays=problem._num_of_relays,
                         max_step=20,
                         population=population,
                         crossover=crossover,
                         selection=selection,
                         mutation=mutation,
                         random_state=seed)

    history = engine.run(generations=config['models']['gens'])

    pareto_front = engine.get_pareto_front()
    best_mr_x = engine.get_sim_solutions()
    solutions = []
    sim_pareto_front = engine.get_sim_pareto()

    best_mr = defaultdict(lambda: float('inf'))
    for obj1, obj2 in best_mr_x:
        best_mr[obj1] = obj2

    end_time = time.time()

    out_dir = os.path.join(WORKING_DIR,  f'{output_dir}/{basename}')

    if save:
        history.dump(os.path.join(out_dir, 'history.json'))
        with open(os.path.join(out_dir, 'time.txt'), mode='w') as f:
            f.write(f"running time: {end_time-start_time:}")

        def my_extract(solution):
            obj1, obj2 = solution.main_obj
            network = solution.decode(obj1)
            edges = []
            for u, v in network.edges:
                edges.append(u)
                edges.append(v)
            return obj1, obj2, network.parent, network.num_childs, network.max_depth, edges


        save_results(pareto_front, solutions, best_mr,
                     out_dir, visualization=False, extract=my_extract)

        visualize_fronts({'nsgaii': sim_pareto_front}, show=False, save=True,
                         title=f'pareto fronts {basename}',
                         filepath=os.path.join(out_dir, 'pareto_fronts.png'),
                         objective_name=['relays', 'energy consumption'])

        # save config
        with open(os.path.join(out_dir, '_config.yml'), mode='w') as f:
            f.write(yaml.dump(config))

        with open(os.path.join(out_dir, 'r.txt'), mode='w') as f:
            f.write('{} {}'.format(problem._num_of_relays, energy_consumption(problem._num_of_sensors, 1, problem._radius * 4)))

        P = [[0, 0],[0, 0]]
        P[0][0], P[0][1] = 1, energy_consumption(problem._num_of_sensors, 1, problem._radius * 4)
        P[1][0], P[1][1] = problem._num_of_relays, energy_consumption(problem._num_of_sensors/problem._num_of_relays, 0, 0)
        with open(os.path.join(out_dir, 'P.txt'), mode='w') as f:
            f.write('{} {}\n{} {}'.format(P[0][0], P[0][1], P[1][0], P[1][1]))

    if save_history:
        save_history_as_gif(history,
                            title="NSGAII - multi-hop",
                            objective_name=['relays', 'energy'],
                            gen_filter=lambda x: (x % 5 == 0),
                            out_dir=out_dir)

    if save or save_history:
        open(os.path.join(out_dir, 'done.flag'), 'a').close()

    return pareto_front

if __name__ == '__main__':
    config = {'data': {'max_hop': 12},
                  'models': {'gens': 100},
		  'encoding': {'init_method': 'DCPrimRST'}}
    solve('data/_tiny/multi_hop/tiny_ga-dem1_r25_1_40.json', model = '1.7.7.0', config=config)
    # solve('data/_medium/multi_hop/medium_ga-dem1_r25_1_40.json', model = '1.7.7.0', config=config)
    # solve('data/test/NIn1_dem1.json', model='1.0.7.0', config=config)

