import glob
import scipy.io.wavfile as wav
import numpy as np
import pyworld as world
import os
import logging

pitches = [-12, -5, 5, 12]

def shift_pitch(path):
    loc, _ = os.path.splitext(path)
    directory, fname = os.path.split(loc)

    logging.info(f'Loading {fname}')
    fs, x = wav.read(path)
    xtype = x.dtype
    int_type = np.issubdtype(xtype, np.integer)

    if int_type:
        info = np.iinfo(xtype)
        x = x / info.max

    if len(x.shape) == 2:
        x = (x[:,0] + x[:,1]) / 2

    logging.info(f'Analyzing {fname}')
    f0, t = world.harvest(x, fs)
    sp = world.cheaptrick(x, f0, t, fs)
    ap = world.d4c(x, f0, t, fs)

    for i in pitches:
        if i == 0:
            continue
        logging.info(f'Synthesizing {fname} {i:+}')
        shift_f0 = f0 * np.exp2(i / 12)
        y = world.synthesize(shift_f0, sp, ap, fs)

        if int_type:
            y = (y * info.max).clip(info.min, info.max).astype(xtype)

        wav.write(loc + f'{i:+}.wav', fs, y)

if __name__ == '__main__':
    logging.basicConfig(format='%(message)s', level=logging.INFO)
    for path in glob.glob('*.wav'):
        shift_pitch(path)

