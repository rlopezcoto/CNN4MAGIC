import gc

import numpy as np
from keras.models import load_model

from CNN4MAGIC.CNN_Models.SeparationStereo.utils import *

net_name = 'single_DenseNet_25_3_doubleDense'

# Load the model
path = '/data/mariotti_data/CNN4MAGIC/CNN_Models/SeparationStereo/checkpoints/' + net_name + '.hdf5'
print('Loading model ' + net_name + '...')
model = load_model(path)

# %% Load Hadron first and make prediction on them
m1_te, m2_te, y_true_h = load_hadrons('test')
print('Making Predictions...')
y_pred_h = model.predict({'m1': m1_te, 'm2': m2_te}, verbose=1)
# Look at misclassified examples
# %%
plot_misclassified_hadrons(m1_te, m2_te, y_pred_h, net_name=net_name)

# %%
del m1_te, m2_te  # Free the memory
gc.collect()
# %%
# Load Gammas
m1_te, m2_te, y_true_g = load_gammas('test')

print('Making Predictions...')
y_pred_g = model.predict({'m1': m1_te, 'm2': m2_te}, verbose=1)

# %%
plot_misclassified_gammas(m1_te, m2_te, y_pred_g, net_name=net_name)

# %%
del m1_te, m2_te
gc.collect()

# %%
# Organize better
y_true = np.vstack((y_true_h, y_true_g))
y_pred = np.vstack((y_pred_h, y_pred_g))

# Plot stuff
print('Plotting gammaness...')
plot_gammaness(y_true, y_true, net_name=net_name)

#%%
print('Plotting confusion matrix...')
plot_confusion_matrix(y_pred, y_true, ['Hadrons', 'Gammas'], net_name='test')

print('All done')
