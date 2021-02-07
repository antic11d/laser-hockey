import numpy as np
from matplotlib import pyplot as plt
from pathlib import Path
import pickle
import shutil
from tabulate import tabulate
import random

mu_norm = np.array([-1.65914335e+00, 3.31981441e-01, 4.70300567e-02, 3.88417447e-01,
                    1.25526876e-01, 4.03919130e-02, 2.92641428e+00, 1.86940286e-01,
                    -1.17453057e-03, -4.41027699e-02, 1.43406859e-01, -7.98745943e-03,
                    2.23126735e-01, 1.49935158e-01, 6.21875702e-01, -5.32693254e-02,
                    1.82178442e+00, 1.11810190e+00])

std_norm = np.array([0.81938143, 1.35541514, 0.61029629, 4.18274236, 3.99964675, 3.6902117,
                     0.82436743, 0.84923757, 0.64665236, 3.97612406, 4.52271474, 3.4465636,
                     1.95700826, 1.65049227, 14.87955476, 13.1330967, 3.95589335, 3.37170976])


def running_mean(x, N):
    cumsum = np.cumsum(np.insert(x, 0, 0))
    return (cumsum[N:] - cumsum[:-N]) / float(N)


def soft_update(target, source, tau):
    for target_param, param in zip(target.parameters(), source.parameters()):
        target_param.data.copy_(
            target_param.data * (1.0 - tau) + param.data * tau
        )


def hard_update(target, source):
    for target_param, param in zip(target.parameters(), source.parameters()):
        target_param.data.copy_(param.data)


def poll_opponent(opponents):
    # TODO: Implement smarter polling
    return random.choice(opponents)


class Logger:
    """
    The Logger class is used printing statistics, saving/loading models and plotting.

    Parameters
    ----------
    prefix_path : Path
        The variable is used for specifying the root of the path where the plots and models are saved.
    mode: str
        The variable specifies in which mode we are currently running. (shooting | defense | normal)
    cleanup: bool
        The variable specifies whether the logging folder should be cleaned up.
    quiet: boolean
        This variable is used to specify whether the prints are hidden or not.
    """

    def __init__(self, prefix_path, mode, cleanup=False, quiet=False) -> None:
        self.prefix_path = Path(prefix_path)

        self.agents_prefix_path = self.prefix_path.joinpath('agents')
        self.plots_prefix_path = self.prefix_path.joinpath('plots')

        self.prefix_path.mkdir(exist_ok=True)

        if cleanup:
            self._cleanup()

        self.quiet = quiet

        if not self.quiet:
            print(f"Running in mode: {mode}")

    # TODO: add logging to file if needed
    def info(self, message):
        print(message)

    def save_model(self, model, filename):
        savepath = self.agents_prefix_path.joinpath(filename).with_suffix('.pkl')
        with open(savepath, 'wb') as outp:
            pickle.dump(model, outp, pickle.HIGHEST_PROTOCOL)

    def print_episode_info(self, game_outcome, episode_counter, step, total_reward, epsilon=None, touched=None):
        if not self.quiet:
            padding = 8 if game_outcome == 0 else 0
            msg_string = '{} {:>4}: Done after {:>3} steps. \tReward: {:<15}'.format(
                " " * padding, episode_counter, step + 1, round(total_reward, 4))

            if touched is not None:
                msg_string = '{}Touched: {:<15}'.format(msg_string, int(touched))

            if epsilon is not None:
                msg_string = '{}Epsilon: {:<5}'.format(msg_string, round(epsilon, 2))

            print(msg_string)

    def print_stats(self, rew_stats, touch_stats, won_stats, lost_stats):
        if not self.quiet:
            print(tabulate([['Mean reward', np.around(np.mean(rew_stats), 3)],
                            ['Mean touch', np.around(np.mean(list(touch_stats.values())), 3)],
                            ['Mean won', np.around(np.mean(list(won_stats.values())), 3)],
                            ['Mean lost', np.around(np.mean(list(lost_stats.values())), 3)]], tablefmt='grid'))

    def load_model(self, filename):
        if filename is None:
            load_path = self.agents_prefix_path.joinpath('agent.pkl')
        else:
            load_path = Path(filename)
        with open(load_path, 'rb') as inp:
            return pickle.load(inp)

    def hist(self, data, title, filename=None, show=True):
        plt.figure()
        plt.hist(data, density=True)
        plt.title(title)

        plt.savefig(self.reward_prefix_path.joinpath(filename).with_suffix('.pdf'))
        if show:
            plt.show()
        plt.close()

    def plot_running_mean(self, data, title, filename=None, show=True):
        data_np = np.asarray(data)
        mean = running_mean(data_np, 50)
        self._plot(mean, title, filename, show)

    def plot(self, data, title, filename=None, show=True):
        self._plot(data, title, filename, show)

    def plot_intermediate_stats(self, data, show=True):
        self._plot((data["won"], data["lost"]), "Evaluation won vs loss", "evaluation-won-loss", show, ylim=(0, 1))

        for key in data.keys() - ["won", "lost"]:
            title = f'Evaluation {key} mean'
            filename = f'evaluation-{key}.pdf'

            self._plot(data[key], title, filename, show)

    def _plot(self, data, title, filename=None, show=True, ylim=None):
        plt.figure()
        # Plotting Won vs lost
        if isinstance(data, tuple):
            plt.plot(data[0], label="Won", color="blue")
            plt.plot(data[1], label="Lost", color='red')
            plt.ylim(*ylim)
            plt.legend()
        else:
            plt.plot(data)
        plt.title(title)

        plt.savefig(self.plots_prefix_path.joinpath(filename).with_suffix('.pdf'))
        if show:
            plt.show()

        plt.close()

    # TODO: REMOVE
    def clean_rew_dir(self):
        print("This function will soon be deprecated")
        shutil.rmtree(self.reward_prefix_path, ignore_errors=True)
        self.reward_prefix_path.mkdir(exist_ok=True)

    def _cleanup(self):
        shutil.rmtree(self.agents_prefix_path, ignore_errors=True)
        shutil.rmtree(self.plots_prefix_path, ignore_errors=True)
        self.agents_prefix_path.mkdir(exist_ok=True)
        self.plots_prefix_path.mkdir(exist_ok=True)
