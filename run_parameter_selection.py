from __future__ import absolute_import

from utils.configurations import load_config, gen_output_dir

import solver_mhn_kruskal
import solver_mhn_gprim4
import solver_mhn_nrk
import solver_mhn_prim
import solver_mhn_prufer
import summarization
import run

import os
from os.path import join
from random import Random
from collections import OrderedDict
import pandas as pd

WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(WORKING_DIR, './configs/_configurations.yml')
DATA_DIR = os.path.join(WORKING_DIR, "./data/small/multi_hop")

def random_tests():
    tests = []
    rand = Random(42)
    for filename in os.listdir(DATA_DIR):
        if 'dem' in filename:
            tests.append(filename)

    return rand.sample(tests, 10)

def choose_pc(solver, model, tests, pc_list, default_pm=0.1, gprim=False):
    pm = default_pm
    config = load_config(CONFIG_FILE, model)
    out_dir = './results/params_selection'

    test_path = './data/params_selection'
    data = [[] for _ in range(len(pc_list))]
    model_name = []

    for i in range(len(pc_list)):
        smodel = '{}.{}.{}'.format(model, i, 1) 
        # out_model_dir = os.path.join(out_dir, smodel)
        if not gprim:
            config['encoding']['cro_prob'] = pc_list[i]
            config['encoding']['mut_prob'] = pm
        else:
            config['encoding']['cro_prob'] = pc_list[i]
            config['encoding']['mut_prob_a'] = pm[0]
            config['encoding']['mut_prob_b'] = pm[1]
        data[i] = run.multi_run_solver(solver, smodel, test_path, 10, None, tests, save_history=False, config=config)
        model_name.append('{}_{}'.format(smodel, pc_list[i]))

    summ_list = []
    for i in range(10):
        model_dict = OrderedDict()
        for j in range(len(pc_list)):
            model_dict[model_name[j]] = data[j][i]
        cname = 'sum_pc_{}_{}'.format(model, i)
        summ_list.append(cname)
        summarization.summarize_model(model_dict, out_dir, cname, tests)

    summarization.calc_average_metrics(
        summ_list, out_dir, f'average_pc_{model}_1-10', tests)
        
def choose_pm(solver, model, tests, pm_list, default_pc=0.7, gprim=False):
    pc = default_pc
    config = load_config(CONFIG_FILE, model)
    out_dir = './results/params_selection'

    model_dict = {}
    test_path = './data/params_selection'
    data = [[] for _ in range(len(pm_list))]
    model_name = []

    for i in range(len(pm_list)):
        smodel = '{}.{}.{}'.format(model, 4, i) 
        # out_model_dir = os.path.join(out_dir, smodel)
        if not gprim:
            config['encoding']['cro_prob'] = pc
            config['encoding']['mut_prob'] = pm_list[i]
        else:
            config['encoding']['cro_prob'] = pc
            config['encoding']['mut_prob_a'] = pm_list[i][0]
            config['encoding']['mut_prob_b'] = pm_list[i][1]
        data[i] = run.multi_run_solver(solver, smodel, test_path, 10, None, tests, save_history=False, config=config)
        model_name.append('{}_{}'.format(smodel, pm_list[i]))

    summ_list = []
    for i in range(10):
        model_dict = OrderedDict()
        for j in range(len(pm_list)):
            model_dict[model_name[j]] = data[j][i]
        cname = 'sum_pm_{}_{}'.format(model, i)
        summ_list.append(cname)
        summarization.summarize_model(model_dict, out_dir, cname, tests)

    summarization.calc_average_metrics(
        summ_list, out_dir, f'average_pm_{model}_1-10', tests)

def choose_parameters(solver, model, tests, gprim=False):
    if not gprim:
        pc_list = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        choose_pc(solver, model, tests, pc_list)
        pm_list = [0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5]
        choose_pm(solver, model, tests, pm_list)
    else:
        pc_list = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        choose_pc(solver, model, tests, pc_list, default_pm=(0.9,0.1), gprim=gprim)
        pm_list = [(0.9, 0.1), (0.8, 0.2), (0.8, 0.1), (0.7, 0.2)]
        choose_pm(solver, model, tests, pm_list, default_pc=0.5, gprim=gprim)

if __name__ == '__main__':
    # tests = random_tests() 
    tests = ['']
    choose_parameters(solver_mhn_gprim4, "1.6.9.0", tests, gprim=True)
    choose_parameters(solver_mhn_kruskal, "1.6.2.0", tests)
    choose_parameters(solver_mhn_prim, "1.6.4.0", tests)
    choose_parameters(solver_mhn_prufer, "1.6.6.0", tests)
    choose_parameters(solver_mhn_nrk, "1.6.1.0", tests)
    summarization.average_tests_score('./results/params_selection/average_pc_1.6.1.0_1-10')
    summarization.average_tests_score('./results/params_selection/average_pc_1.6.2.0_1-10')
    summarization.average_tests_score('./results/params_selection/average_pc_1.6.4.0_1-10')
    summarization.average_tests_score('./results/params_selection/average_pc_1.6.6.0_1-10')
    summarization.average_tests_score('./results/params_selection/average_pc_1.6.9.0_1-10')
    summarization.average_tests_score('./results/params_selection/average_pm_1.6.1.0_1-10')
    summarization.average_tests_score('./results/params_selection/average_pm_1.6.2.0_1-10')
    summarization.average_tests_score('./results/params_selection/average_pm_1.6.4.0_1-10')
    summarization.average_tests_score('./results/params_selection/average_pm_1.6.6.0_1-10')
    summarization.average_tests_score('./results/params_selection/average_pm_1.6.9.0_1-10')
