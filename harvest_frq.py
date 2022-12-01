import logging
logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO, datefmt='%x %a %X')
if __name__ == '__main__':
    logging.info('Importing packages')
import numpy as np
import scipy.io.wavfile as wav
import pyworld as world
import sys
import time
import struct
import os
import traceback
import concurrent.futures
from argparse import ArgumentParser

def base_frq(f0, f0_min=None, f0_max=880):
    value = 0
    r = 1
    p = [0, 0, 0, 0, 0, 0]
    q = 0
    avg_frq = 0
    base_value = 0

    if not f0_min:
        f0_min = world.default_f0_floor

    if not f0_max:
        f0_max = world.default_f0_ceil
    
    for i in range(0, len(f0)):
        value = f0[i]
        if value <= f0_max and value >= f0_min:
            r = 1

            for j in range(0, 6):
                if i > j:
                    q = f0[i - j - 1] - value
                    p[j] = value / (value + q * q)
                else:
                    p[j] = 1 / (1 + value)
                    
                r *= p[j]

            avg_frq += value * r
            base_value += r

    if base_value > 0:
        avg_frq /= base_value
    return avg_frq

def frq_gen(floc, f0_max=880, hop=256):
    t0 = time.perf_counter()
    fname, _ = os.path.splitext(floc)
    basename = os.path.basename(fname)
    logging.info(f'Making {basename}_wav.frq 1/4')
    fs, x = wav.read(floc)
    xtype = x.dtype
    int_type = np.issubdtype(xtype, np.integer)

    if int_type:
        info = np.iinfo(xtype)
        x = x / info.max

    if len(x.shape) == 2:
        x = (x[:,0] + x[:,1]) / 2

    logging.info(f'Making {basename}_wav.frq 2/4')
    frame_period = 1000 * hop / fs
    f0, t = world.harvest(x, fs, f0_ceil=f0_max, frame_period=frame_period)
    base_f0 = base_frq(f0, f0_max=f0_max)

    logging.info(f'Making {basename}_wav.frq 3/4')
    sp = world.cheaptrick(x, f0, t, fs)
    amp = np.mean(np.sqrt(sp), axis=1)

    logging.info(f'Making {basename}_wav.frq 4/4')
    with open(fname + '_wav.frq', 'wb') as f:
        f.write(b'FREQ0003')
        f.write(struct.pack('i', hop))
        f.write(struct.pack('d', base_f0))
        f.write(bytes(16))
        f.write(struct.pack('i', f0.shape[0]))
        for i in range(0, f0.shape[0]):
            f.write(struct.pack('2d', f0[i], amp[i]))
    t = time.perf_counter()
    logging.info(f'{basename}_wav.frq finished at {t - t0:.3f} seconds.')

if __name__ == '__main__':
    try:
        parser = ArgumentParser(description="Generate .frq files using WORLD's Harvest F0 estimation algorithm.")
        parser.add_argument('vb', help='The voicebank location')
        parser.add_argument('--single-thread', '-s', action='store_true', help='Run single threaded')

        args, _ = parser.parse_known_args()
        samples = []
        logging.info('Listing all samples')
        for root, dirs, files in os.walk(args.vb):
            for file in files:
                if file.endswith('.wav'):
                    fname, _ = os.path.splitext(file)
                    samples.append(os.path.join(root, file))
        if args.single_thread:
            logging.info('Running single threaded')
            t0 = time.perf_counter()
            for sample in samples:
                frq_gen(sample)
            t = time.perf_counter()
        else:
            logging.info('Starting process pool')
            t0 = time.perf_counter()
            with concurrent.futures.ProcessPoolExecutor() as executor:
                executor.map(frq_gen, samples)
            t = time.perf_counter()
        logging.info(f'Whole operation took {t - t0:.3f} seconds.')
        os.system('pause')
    except Exception as e:
        for i in traceback.format_exception(e.__class__, e, e.__traceback__):
            print(i, end='')
        os.system('pause')
