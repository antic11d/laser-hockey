import os
import torch
from laserhockey import hockey_env as h_env
from sac_agent import SACAgent
from importlib import reload
from argparse import ArgumentParser
import sys
from trainer import SACTrainer

# TODO: fix if possible, not the best way of importing
sys.path.insert(0, '.')
sys.path.insert(1, '..')
from utils.utils import *

parser = ArgumentParser()
parser.add_argument('--dry-run', help='Set if running only for sanity check', action='store_true')
parser.add_argument('--cuda', help='Set if want to train on graphic card', action='store_true')
parser.add_argument('--show', help='Set if want to render training process', action='store_true')
parser.add_argument('--q', help='Quiet mode (no prints)', action='store_true')
parser.add_argument('--evaluate', help='Set if want to evaluate agent after the training', action='store_true')
parser.add_argument('--mode', help='Mode for training currently: (shooting | defense | normal)', default='defense')

# Training params
parser.add_argument('--max_episodes', help='Max episodes for training', type=int, default=5000)
parser.add_argument('--max_steps', help='Max steps for training', type=int, default=160)
parser.add_argument('--iter_fit', help='Iter fit', type=int, default=16)
parser.add_argument('--eval_episodes', help='Set number of evaluation episodes', type=int, default=30)
parser.add_argument('--learning_rate', help='Learning rate', type=float, default=3e-4)
parser.add_argument('--update_target_every', help='# of steps between updating target net', type=int, default=1)
parser.add_argument('--gamma', help='Discount', type=float, default=0.99)
parser.add_argument('--batch_size', help='batch_size', type=int, default=64)
parser.add_argument(
    '--alpha',
    type=float,
    default=0.2,
    help='Temperature parameter α determines the relative importance of the entropy term against the reward')
parser.add_argument('--automatic_entropy_tuning', type=bool, default=False,
                    help='Automatically adjust alpha')
parser.add_argument('--soft_tau', help='tau', type=float, default=0.005)
parser.add_argument('--per', help='Utilize Prioritized Experience Replay', action='store_true')
parser.add_argument('--per_alpha', help='Alpha for PER', type=float, default=0.6)

opts = parser.parse_args()


if __name__ == '__main__':
    if opts.dry_run:
        opts.max_episodes = 10

    if opts.mode == 'normal':
        mode = h_env.HockeyEnv_BasicOpponent.NORMAL
    elif opts.mode == 'shooting':
        mode = h_env.HockeyEnv_BasicOpponent.TRAIN_SHOOTING
    elif opts.mode == 'defense':
        mode = h_env.HockeyEnv_BasicOpponent.TRAIN_DEFENSE
    else:
        raise ValueError('Unknown training mode. See --help')

    opts.device = torch.device('cuda' if opts.cuda and torch.cuda.is_available() else 'cpu')
    logger = Logger(prefix_path=os.path.dirname(os.path.realpath(__file__)) + '/logs', mode=opts.mode, quiet=opts.q)
    opponent = h_env.BasicOpponent(weak=False)
    env = h_env.HockeyEnv(mode=mode, quiet=opts.q)

    agent = SACAgent(
        opponent=opponent,
        logger=logger,
        obs_dim=env.observation_space.shape,
        action_dim=env.action_space.shape[0],
        action_space=env.action_space,
        userconfig=vars(opts)
    )
    trainer = SACTrainer(logger, vars(opts))
    trainer.train(agent, env, opts.evaluate)