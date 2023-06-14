import logging
logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO, datefmt='%x %a %X')
if __name__ == '__main__':
    logging.info('Importing packages')
import numpy as np
import soundfile as sf
import scipy.signal as signal
import scipy.fft as fft
from scipy.special import expn
import os
import sys
import time
import traceback
from multiprocessing import freeze_support
import concurrent.futures
from argparse import ArgumentParser, RawDescriptionHelpFormatter

def logmmse(x, sr): # translation of https://raw.githubusercontent.com/braindead/Noise-reduction/master/logmmse.m
    length = int(np.floor(20 * sr / 1000)) # frame size in samples
    if length & 1 == 1:
        length += 1
    PERC = 50 # window overlap in percent of frame size
    len1 = int(np.floor(length * PERC / 100))
    len2 = length - len1 # update rate in samples

    win = np.hanning(length) # define window

    # Noise magnitude calculations - assuming that the first 6 frames is noise/silence
    
    nFFT = 2 * length
    noise_mean = np.zeros(nFFT, dtype=np.float64)
    j = 0
    for m in range(6):
        noise_mean += np.abs(fft.fft(win * x[j:j+length], nFFT, axis=0))
        j += length
    noise_mu = noise_mean / 6
    noise_mu2 = np.square(noise_mu)

    # allocate memory and initialize various variables
    
    x_old = np.zeros(len1, dtype=np.float64)
    Xk_prev = np.zeros((len1, 1), dtype=np.float64)
    NFrames = int(np.floor(len(x) / len2) - np.floor(length / len2))
    xfinal = np.zeros(NFrames * len2, dtype=np.float64)

    # start processing

    k = 0
    aa = 0.98
    mu = 0.98
    eta = 0.15

    ksi_min = 10 ** (-25 / 10)

    for n in range(NFrames):
        insign = win * x[k:k+length]

        spec = fft.fft(insign, nFFT)
        sig = np.abs(spec) # compute the magnitude
        sig2 = np.square(sig)

        gammak = np.minimum(sig2 / noise_mu2, 40) # limit post SNR to avoid overflows

        if n == 0:
            ksi = aa + (1 - aa) * np.maximum(gammak - 1, 0)
        else:
            ksi = aa * Xk_prev / noise_mu2 + (1 - aa) * np.maximum(gammak - 1, 0) # a priori SNR
            ksi = np.maximum(ksi_min, ksi) # limit ksi to -25 dB

        log_sigma_k = gammak * ksi / (1 + ksi) - np.log(1 + ksi)
        vad_decision = np.sum(log_sigma_k) / length
        if vad_decision < eta:
            # noise only frame found
            noise_mu2 = mu * noise_mu2 + (1 - mu) * sig2
        # end of vad

        A = ksi / (1 + ksi) # Log-MMSE estimator
        vk = A * gammak
        ei_vk = 0.5 * expn(1, vk)
        hw = A * np.exp(ei_vk)

        sig = sig * hw
        Xk_prev = np.square(sig)

        xi_w = fft.ifft(hw * spec, nFFT, axis=0)
        xi_w = np.real(xi_w)

        xfinal[k:k+len2] = x_old + xi_w[:len1]
        x_old = xi_w[len1:length]
        k += len2

    return xfinal
    
def remove_noise(path):
    t0 = time.perf_counter() # Time operation
    # Deal with filename
    directory, fname = os.path.split(path)
    logging.info(f'Denoising {fname}')
    new_fname = f'clean_{fname}'
    new_path = os.path.join(directory, new_fname)

    # Setup file
    data, fs = sf.read(path)

    # Deal with multi-channel wavs... kinda.
    if len(data.shape) == 2:
        data = np.mean(data, axis=1)
    
    # Setup highpass
    nyq = 0.5 * fs
    cutoff = 100 / nyq
    sos = signal.butter(2, cutoff, btype='high', output='sos')

    # Highpass, Noise remove, Clip
    data = signal.sosfiltfilt(sos, data)
    data = logmmse(data, fs)

    # Save on new path, delete old path. Safety reasons
    sf.write(new_path, data, fs)
    os.remove(path)
    os.rename(new_path, path)
    t = time.perf_counter()
    logging.info(f'Denoising {fname} took {t - t0:.3f} seconds')

def process_directory(args):
    samples = []
    logging.info('Received directory. Listing files')
    for root, dirs, files in os.walk(args.path):
        for file in files:
            if file.endswith('.wav'):
                samples.append(os.path.join(root, file))
    logging.info(f'Listed {len(samples)} file{"s" if len(samples) != 1 else ""}')

    if args.single_thread or args.num_threads == 1:
        logging.info('Running single threaded')
        t0 = time.perf_counter()
        for sample in samples:
            remove_noise(sample)
        t = time.perf_counter()
    else:
        logging.info('Starting process pool with {args.num_threads} threads.')
        t0 = time.perf_counter()
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.num_threads) as executor:
            executor.map(remove_noise, samples)
        t = time.perf_counter()
    logging.info(f'Whole operation took {t - t0:.3f} seconds')

if __name__ == '__main__':
    freeze_support()
    try:
        parser = ArgumentParser(description='Denoises all wave files in a directory using the Log-MMSE algorithm.\nAssumes the first 120 ms of the samples are pure noise.', formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument('path', help='The path to a .wav file or a directory with .wav files.')
        parser.add_argument('--single-thread', '-s', action='store_true', help='Run single threaded')
        parser.add_argument('--num-threads', '-n', type=int, default=os.cpu_count(), help='How many threads to use. Default is your thread count.')

        args, _ = parser.parse_known_args()
        if os.path.isfile(args.path):
            logging.info('Received file')
            remove_noise(args.path)
        else:
            process_directory(args)
        os.system('pause')
    except Exception as e:
        for i in traceback.format_exception(e.__class__, e, e.__traceback__):
            print(i, end='')
        os.system('pause')
