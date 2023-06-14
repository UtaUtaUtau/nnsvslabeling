import logging
logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO, datefmt='%x %a %X')
if __name__ == '__main__':
    logging.info('Importing packages')
import numpy as np
import soundfile as sf
import pyworld as world
import sys
import time
import struct
import os
import traceback
from multiprocessing import freeze_support
import concurrent.futures
from argparse import ArgumentParser

f0_floor = world.default_f0_floor
f0_ceil = world.default_f0_ceil

def base_frq(f0, f0_min=None, f0_max=None):
    q = 0
    avg_frq = 0
    tally = 0
    N = len(f0)

    if f0_min is None:
        f0_min = f0_floor

    if f0_max is None:
        f0_max = f0_ceil
    
    for i in range(N):
        if f0[i] >= f0_min and f0[i] <= f0_max:
            if i < 1:
                q = f0[i+1] - f0[i]
            elif i == N - 1:
                q = f0[i] - f0[i-1]
            else:
                q = (f0[i+1] - f0[i-1]) / 2
            weight = 2 ** (-q * q)
            avg_frq += f0[i] * weight
            tally += weight

    if tally > 0:
        avg_frq /= tally
    return avg_frq

def frq_gen(floc, f0_max=880, hop=256):
    t0 = time.perf_counter()
    fname, _ = os.path.splitext(floc)
    basename = os.path.basename(fname)
    logging.info(f'Making {basename}_wav.frq 1/4')
    x, fs = sf.read(floc)

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

def process_directory(args):
    samples = []
    logging.info('Received directory. Listing files')
    for root, dirs, files in os.walk(args.path):
        for file in files:
            if file.endswith('.wav'):
                fname, _ = os.path.splitext(file)
                samples.append(os.path.join(root, file))
    logging.info(f'Listed {len(samples)} file{"s" if len(samples) != 1 else ""}')
                
    if args.single_thread or args.num_threads == 1:
        logging.info('Running single threaded')
        t0 = time.perf_counter()
        for sample in samples:
            frq_gen(sample)
        t = time.perf_counter()
    else:
        logging.info('Starting process pool with {args.num_threads} threads.')
        t0 = time.perf_counter()
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.num_threads) as executor:
            executor.map(frq_gen, samples)
        t = time.perf_counter()
    logging.info(f'Whole operation took {t - t0:.3f} seconds.')

if __name__ == '__main__':
    freeze_support()
    try:
        parser = ArgumentParser(description="Generate .frq files using WORLD's Harvest F0 estimation algorithm.")
        parser.add_argument('path', help='The path to a .wav file or a directory with .wav files.')
        parser.add_argument('--single-thread', '-s', action='store_true', help='Run single threaded')
        parser.add_argument('--num-threads', '-n', type=int, default=os.cpu_count() // 3, help='How many threads to use. Default is a third of your thread count.')

        args, _ = parser.parse_known_args()
        if os.path.isfile(args.path):
            logging.info('Received file')
            frq_gen(args.path)
        else:
            process_directory(args)
        os.system('pause')
    except Exception as e:
        for i in traceback.format_exception(e.__class__, e, e.__traceback__):
            print(i, end='')
        os.system('pause')
