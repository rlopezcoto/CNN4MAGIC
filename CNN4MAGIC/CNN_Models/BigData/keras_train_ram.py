import pickle

import numpy as np
from keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau, TerminateOnNaN

from CNN4MAGIC.CNN_Models.BigData.loader import load_data_test, load_data_val, load_data_train
from CNN4MAGIC.CNN_Models.BigData.stereo_models import magic_mobile_singleStem
from CNN4MAGIC.CNN_Models.BigData.utils import plot_hist2D, plot_gaussian_error

# %%
# LOAD DATA
m1_tr, m2_tr, energy_tr = load_data_train(pruned=True)
m1_val, m2_val, energy_val = load_data_val(pruned=True)

energy_tr = np.log10(energy_tr)
energy_val = np.log10(energy_val)
# %%
# LOAD and COMPILE model
# m1 = Input(shape=(67, 68, 2), name='m1')
# energy_regressor = magic_mobile()

num_filt = 136
# energy_regressor = magic_inception(num_filt, num_classes=1, dropout=0, do_res=False)
# energy_regressor.compile(optimizer='adam', loss='mse')
energy_regressor = magic_mobile_singleStem()
energy_regressor.compile(optimizer='adam', loss='mse')

energy_regressor.summary()

# %%

net_name = 'mobileCBAM-fullyCNN-SingleStem-long-wide'
early_stop = EarlyStopping(patience=8, min_delta=0.0001)
nan_stop = TerminateOnNaN()
check = ModelCheckpoint('/data/mariotti_data/CNN4MAGIC/CNN_Models/BigData/checkpoints/' + net_name + '.hdf5',
                        period=3,
                        save_best_only=True)
reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.4,
                              patience=4, min_lr=0.000005)
# [:,:,:,1].reshape((134997, 67, 68, 1))
result = energy_regressor.fit({'m1': m1_tr, 'm2': m2_tr}, energy_tr,
                              batch_size=512,
                              epochs=100,
                              verbose=1,
                              validation_data=({'m1': m1_val, 'm2': m2_val}, energy_val),
                              callbacks=[early_stop, nan_stop, reduce_lr, check])

# %% Save and plot stuff

m1_te, m2_te, energy_te = load_data_test()
y_test = np.log10(energy_te)

print('Making Predictions...')
y_pred = energy_regressor.predict({'m1': m1_te, 'm2': m2_te})

# %%
print('Plotting stuff...')
plot_hist2D(y_test, y_pred, fig_folder='/data/mariotti_data/CNN4MAGIC/CNN_Models/BigData/pics/', net_name=net_name,
            num_bins=100)

plot_gaussian_error(y_test, y_pred, net_name=net_name + '_10bin', num_bins=10,
                    fig_folder='/data/mariotti_data/CNN4MAGIC/CNN_Models/BigData/pics/')

# %%
print('Saving History')
with open('/data/mariotti_data/CNN4MAGIC/CNN_Models/BigData/' + net_name + '_history.pkl', 'wb') as f:
    pickle.dump(result, f, protocol=4)

print('All done, everything went fine.')
