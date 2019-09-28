import pickle
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt


def pickle_read(filepath):
    with open(filepath, 'rb') as f:
        return pickle.load(f)


def pickle_dump(filepath, object):
    with open(filepath, 'wb') as f:
        pickle.dump(object, f, protocol=pickle.HIGHEST_PROTOCOL)


def significance(energy_threshold, theta_sq_threshold, gammaness_threshold, energy_estimated, theta_sq_on,
                 theta_sq_off_global, gammaness):
    on_events = np.sum(
        (energy_estimated.flatten() > energy_threshold) & (theta_sq_on.flatten() < theta_sq_threshold) & (
                gammaness.flatten() > gammaness_threshold))
    off_events = np.sum(
        (energy_estimated.flatten() > energy_threshold) & (theta_sq_off_global.flatten() < theta_sq_threshold) & (
                gammaness.flatten() > gammaness_threshold))

    return (on_events - off_events) / np.sqrt(off_events)


def maximize_gridsearch(energy_estimated, theta_sq_on, theta_sq_off_global, gammaness, num_grid_steps=10):
    en_range = np.linspace(np.min(energy_estimated), np.max(energy_estimated), num_grid_steps)
    th_range = np.linspace(np.min(theta_sq_on), 0.5, num_grid_steps)
    chi_range = np.linspace(0.1, 10, num_grid_steps)
    gammaness_range = 1 - 10 ** -chi_range

    s_search = np.zeros((num_grid_steps, num_grid_steps, num_grid_steps))

    for i, e_th in enumerate(tqdm(en_range)):
        for j, t_th in enumerate(th_range):
            for k, g_th in enumerate(gammaness_range):
                s_search[i, j, k] = significance(e_th, t_th, g_th, energy_estimated, theta_sq_on, theta_sq_off_global,
                                                 gammaness)

    max_significance = np.max(s_search[~np.isnan(s_search) & ~np.isinf(s_search)])
    idxs = np.where(s_search == max_significance)
    print(f'Energy th: {en_range[idxs[0]]}\nTheta2 cut: {th_range[idxs[1]]}\nGammaness cut: {gammaness_range[idxs[2]]}')
    return max_significance, en_range[idxs[0]], th_range[idxs[1]], gammaness_range[idxs[2]]


# %%


def optimize_significance(net_name):
    theta_sq_on = pickle_read('/data4T/CNN4MAGIC/results/MC_classification/crab_reconstructions/theta_sq_on.pkl')
    # theta_sq_off_3 = pickle_read('/data4T/CNN4MAGIC/results/MC_classification/crab_reconstructions/theta_sq_3_off.pkl')
    theta_sq_off_global = pickle_read(
        '/data4T/CNN4MAGIC/results/MC_classification/crab_reconstructions/theta_sq_off_global.pkl')
    # note: theta_sq_off_global = (theta_sq_off1 + theta_sq_off2 + theta_sq_off3) / 3
    # off_1 = pickle_read('/data4T/CNN4MAGIC/results/MC_classification/crab_reconstructions/off_1.pkl')
    # off_2 = pickle_read('/data4T/CNN4MAGIC/results/MC_classification/crab_reconstructions/off_2.pkl')
    off_3 = pickle_read('/data4T/CNN4MAGIC/results/MC_classification/crab_reconstructions/off_3.pkl')
    energy_estimated = pickle_read(
        '/data4T/CNN4MAGIC/results/MC_classification/crab_reconstructions/crab_energy_transfer-SE-inc-v3-snap-lowLR_SWA.pkl')
    gammaness = pickle_read(
        f'/data4T/CNN4MAGIC/results/MC_classification/experiments/{net_name}/computed_data/crab_separation_{net_name}.pkl')

    tr_ratio_wrt_total = .60

    theta_sq_off_chosen = off_3
    theta_sq_off_chosen_limato = theta_sq_off_chosen[:len(gammaness)]
    theta_sq_on_limato = theta_sq_on[:len(gammaness)]
    energy_estimated_limato = energy_estimated[:len(gammaness)]

    num_values_tr = int(len(gammaness) * tr_ratio_wrt_total)

    en_train = energy_estimated_limato[:num_values_tr]
    en_val = energy_estimated_limato[num_values_tr:]

    theta_sq_on_train = theta_sq_on_limato[:num_values_tr]
    theta_sq_on_val = theta_sq_on_limato[num_values_tr:]

    theta_sq_off_global_train = theta_sq_off_chosen_limato[:num_values_tr]
    theta_sq_off_global_val = theta_sq_off_chosen_limato[num_values_tr:]

    gammaness_train = gammaness[:num_values_tr]
    gammaness_val = gammaness[num_values_tr:]
    # %
    s_train, e_cut, th_cut, gamma_cut = maximize_gridsearch(en_train, theta_sq_on_train, theta_sq_off_global_train,
                                                            gammaness_train, num_grid_steps=40)
    # %
    s_val = significance(e_cut, th_cut, gamma_cut, en_val, theta_sq_on_val, theta_sq_off_global_val, gammaness_val)
    # %
    print(s_train, s_val)

    # %
    gammaness_list = [gamma_cut]
    num_bins = 50
    energy_th = e_cut
    thetha_cut = th_cut
    for gammaness_single in tqdm(gammaness_list):
        is_gamma = gammaness_val.flatten() > gammaness_single
        energy_ok = en_val.flatten() > energy_th
        theta_sq_off_all = theta_sq_off_global_val

        print(np.sum(is_gamma & energy_ok))
        plt.figure()
        plt.hist(theta_sq_off_all, alpha=0.5, weights=1 / 3 * np.ones(len(theta_sq_off_all)),
                 bins=np.linspace(0, 0.16, num_bins), log=False, label='$\Theta^2$ Off')
        plt.hist(theta_sq_on_val[is_gamma & energy_ok], alpha=1, histtype='step', bins=np.linspace(0, 0.16, num_bins),
                 log=False,
                 color='C3', label='$\Theta^2$ Signal')
        plt.hist(theta_sq_on_val[is_gamma & energy_ok], alpha=0.15, histtype='stepfilled',
                 bins=np.linspace(0, 0.16, num_bins),
                 log=False,
                 color='C3')

        plt.xlim([0, thetha_cut * 2])
        plt.vlines(thetha_cut, 0, 190, linestyles='-.', label='$\Theta^2$ Off', alpha=0.6)
        # plt.ylim([0, 110])
        plt.xlabel('$\Theta^2$')
        plt.ylabel('Counts')
        plt.legend()
        plt.title(f'$\Theta^2$ plot')
        plt.savefig(
            f'/data4T/CNN4MAGIC/results/MC_classification/crab_reconstructions/plots/significances/theta2_crab_{net_name}_tr_va.png')

    return s_train, s_val, e_cut, th_cut, gamma_cut


# %%
import os

experiment_names = os.listdir('/data4T/CNN4MAGIC/results/MC_classification/experiments')
#%%
experiment_names.remove('EfficientNet_B1')
experiment_names.remove('EfficientNet_B0')
experiment_names.remove('EfficientNet_B0_dropout06')
#%%
results_global = {name: optimize_significance(name) for name in experiment_names}

# %
import pandas as pd

#%%
df = pd.DataFrame(results_global).transpose()
df.columns = ['S_tr','S_va','E_cut','Th_cut','Gamma_cut']
# %% Try with scipy optimize

from scipy.optimize import minimize


def significance_forscipy(ths, energy_estimated, theta_sq_on, theta_sq_off_global, gammaness):
    energy_threshold = ths[0]
    theta_sq_threshold = ths[1]
    gammaness_threshold = ths[2]
    on_events = np.sum(
        (energy_estimated.flatten() > energy_threshold) & (theta_sq_on.flatten() < theta_sq_threshold) & (
                gammaness.flatten() > gammaness_threshold))
    off_events = np.sum(
        (energy_estimated.flatten() > energy_threshold) & (theta_sq_off_global.flatten() < theta_sq_threshold) & (
                gammaness.flatten() > gammaness_threshold))
    return (on_events - off_events) / np.sqrt(off_events)


fun = lambda x: -significance_forscipy(x, energy_estimated=en_train, theta_sq_on=theta_sq_on_train,
                                       theta_sq_off_global=theta_sq_off_global_train, gammaness=gammaness_train)

# %%
result = minimize(fun,
                  np.array([1, 0.1, 0.9]),
                  method='Nelder-Mead',
                  options={'maxfev': 1e6, 'maxiter': 1e6, 'disp': True})
# %%
result.x
