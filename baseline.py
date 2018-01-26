import main as conv_graph
import argparse
import json
import numpy as np
import os
import logging
import itertools

# I chose to hardcode the parameters so we can all agree on a baseline and share a record of it.
# Use "default" mode as our shared baseline -- these settings shouldn't really be changed.
# Use "test" mode  to ensure that all the models are working, it will be quick (a minute or two)
# Use "freeplay" mode to mess around with the parameters and try to improve our settings.

default = {"num_experiments": 10,
           "models": ['mlp', 'sgc', 'slr', 'cgn', 'lcg'],
           "datasets": ['random', 'percolate', 'tcga-gbm'],
           "vars_to_explore": [('lr', (1e-5, 1e-3))],
           "epoch": 10,
           "batch_size": 100
           }
test = {"num_experiments": 1,
        "models": ['mlp', 'sgc', 'slr', 'cgn', 'lcg'],
        "datasets": ['random', 'percolate', 'tcga-gbm'],
        "vars_to_explore": [('lr', (1e-5, 1e-3))],
        "epoch": 1,
        "batch_size": 10
        }
freeplay = {"num_experiments": 10,
            "models": ['mlp', 'sgc', 'slr', 'cgn', 'lcg'],
            "datasets": ['random', 'percolate', 'tcga-gbm'],
            "vars_to_explore":[('lr', (1e-5, 1e-3))],
            "epoch": 10,
            "batch_size": 100}


def build_parser():
    parser = conv_graph.build_parser()
    parser.add_argument('--mode', default="default", help="The type of baseline tests to launch", choices=['default', 'test', 'freeplay'])
    return parser

def parse_args(argv):
    opt = build_parser().parse_args(argv)
    return opt

def main(argv=None):
    # Setup logger
    hdlr = logging.FileHandler('baseline.log')
    hdlr.setFormatter(logging.Formatter("%(message)s"))
    logger = logging.getLogger('baseline')
    logger.addHandler(hdlr)
    logger.setLevel('INFO')

    opt = parse_args(argv)
    mode = globals()[opt.mode]
    setting = vars(opt)
    setting['epoch'] = mode['epoch']
    setting['batch_size'] = mode['batch_size']
    del setting['mode']
    max_valid_acc = 0
    best_summary = {}
    best_hyper_parameters = {}

    for model, dataset, seed in itertools.product(mode['models'], mode['datasets'], range(0, mode['num_experiments'])):
        setting['model'] = model
        setting['dataset'] = dataset
        setting['seed'] = seed
        for variable, bound in mode['vars_to_explore']:
            min_value, max_value = bound
            if min_value > max_value:
                raise ValueError("The minimum value is bigger than the maxium value for {}, {}".format(value, bound))
            set_num_channel(model, setting)

            # sampling the value
            if type(min_value) == int and type(max_value) == int:
                value = min_value + np.random.random_sample() * (max_value - min_value)
                value = int(np.round(value))
            else:
                value = np.exp(np.log(min_value) + (np.log(max_value) - np.log(min_value)) * np.random.random_sample())
                value = float(value)

            if variable not in setting:
                raise ValueError("The parameter {} is nor defined.".format(variable))

            setting[variable] = value
            summary = conv_graph.main(opt)
            if max_valid_acc < summary['accuracy']['valid']:
                max_valid_acc = summary['accuracy']['valid']
                best_summary = summary
                best_hyper_parameters = setting
                print seed
                print best_summary
                print best_hyper_parameters

        # if this round of experiments is finished, log and reset
        if seed + 1 == mode['num_experiments']:
            log_summary(best_summary, best_hyper_parameters)
            max_valid_acc = 0
            best_summary = {}
            best_hyper_parameters = {}

def log_summary(summary, hyper):
    logger = logging.getLogger('baseline')
    logger.info("model: {}, dataset: {}, train: {}, valid: {}, test: {}".format(hyper['model'], hyper['dataset'], summary['accuracy']['train'], summary['accuracy']['valid'], summary['accuracy']['tests']))
    logger.info(summary)
    logger.info(hyper)
    logger.info("")

def set_num_channel(model, setting):
    num_channel = setting['num_channel']
    if model == 'sgc':
        setting['num_channel'] = 1
    else:
        setting['num_channel'] = num_channel

if __name__ == "__main__":
    main()
