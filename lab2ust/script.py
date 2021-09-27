import pyutau
import traceback
import time
import sys
import os
import math

def quantize(x):
    return int(round(x / 15)) * 15

try:
    plugin = pyutau.UtauPlugin(sys.argv[-1])
    lab = open(input('Drag and drop the .lab file here: ').strip('"')).readlines()
    phonemes = []
    duration = []
    ups = 480 * float(plugin.settings['Tempo']) / 60
    
    #Save phonemes in duration in list. Convert durations to note lengths
    for i in lab:
        ph = i.strip().split()
        phonemes.append(ph[2])
        duration.append((float(ph[1]) - float(ph[0])) / (10 ** 7))
        duration[-1] *= ups

    #Try to figure if it's a Japanese label or not.
    jpn = True
    for i in phonemes:
        if i != 'N' and i.lower() != i:
            jpn = False
            break

    #Ask if fusing
    if jpn:
        print('Detected a Japanese label.')
    else:
        print('Detected a different language.')
        
    fuse = input('Automatically fuse? [y/n] ')
    if fuse.lower() == 'y':
        if jpn:
        #Fuse CVs
            vowels = ['a', 'i', 'u', 'e', 'o']
            standalone = ['N', 'cl', 'pau', 'br', 'vf', 'sil']
            for i in range(len(duration) - 1, -1, -1):
                if phonemes[i][0] not in vowels:
                    if phonemes[i] in standalone:
                        continue
                    else:
                        if phonemes[i+1][0] in vowels:
                            phonemes[i+1] = phonemes[i] + phonemes[i+1]
                            duration[i-1] += duration[i]
                            del duration[i]
                            del phonemes[i]
        else:
            vowels = None
            standalone = ['cl', 'pau', 'br', 'vf', 'sil']
            phoneme_mode = input('Select phoneme set\n1: Arpabet\n2: X-Sampa\n')
            if phoneme_mode == '1':
                vowels = ['aa', 'ae', 'ah', 'ao', 'ax', 'eh', 'er', 'ih', 'iy', 'uh', 'uw', 'aw', 'ay', 'ey', 'ow', 'oy']
            else:
                vowels = ['i', 'y', '1', '}', 'M', 'u', 'I', 'Y', 'I\\', 'U\\', 'U', 'e', '2', '@\\', '8', '7', 'o', 'e_o', '2_o', '@', 'o_o', 'E', '9', '3', '3\\', 'V', 'O', '{', '6', 'a', '&', 'a_"', 'A', 'Q']
            phoneme_ranges = []
            duration_ranges = []
            i = 0
            #Get ranges hopefully
            while i < len(phonemes):
                if phonemes[i] in standalone:
                    phoneme_ranges.append((i, i))
                    duration_ranges.append((i, i))
                else:
                    if phonemes[i] in vowels:
                        onset = 0
                        coda = 0
                        start = True
                        end = True
                        for j in range(i-1, -1, -1):
                            if phonemes[j] in vowels:
                                start = False
                                break
                            if phonemes[j] in standalone:
                                break
                            else:
                                onset += 1
                        for j in range(i+1, len(phonemes)):
                            if phonemes[j] in vowels:
                                end = False
                                break
                            if phonemes[j] in standalone:
                                break
                            else:
                                coda += 1
                        if not start:
                            onset = math.ceil(onset / 2)
                        if not end:
                            coda = math.floor(coda / 2)
                        phoneme_ranges.append((i-onset, i+coda))
                        duration_ranges.append((i, i+coda))
                i += 1

            #Correct duration ranges
            for i in range(0, len(duration_ranges) - 1):
                curr_range = duration_ranges[i]
                next_range = duration_ranges[i+1]
                duration_ranges[i] = (curr_range[0], next_range[0]-1)
                
            #Make new set
            new_phonemes = []
            new_duration = []
            for i in phoneme_ranges:
                new_phonemes.append(' '.join(phonemes[i[0]:i[1]+1]))
            for i in duration_ranges:
                new_duration.append(math.fsum(duration[i[0]:i[1]+1]))
            phonemes = new_phonemes
            duration = new_duration
                            
    #Compensate duration for decimal to integer
    for i in range(0, len(duration) - 1):
        int_dur = int(duration[i])
        error = duration[i] - int_dur
        duration[i] = int_dur
        duration[i+1] += error

    duration[-1] = int(duration[-1])
    #Compensate duration for UTAU note lower limit
    for i in range(len(duration) - 1, -1, -1):
        if duration[i] < 15:
            error = 15 - duration[i]
            duration[i-1] -= error
            duration[i] = 15

    #Compensate for quantization
    for i in range(0, len(duration) - 1):
        quant_dur = quantize(duration[i])
        error = duration[i] - quant_dur
        duration[i] = quant_dur
        duration[i+1] += error

    duration[-1] = quantize(duration[-1])
    
    for i in range(0, len(duration)):
        note = pyutau.create_note(phonemes[i] if phonemes[i] != 'pau' else 'R', duration[i])
        plugin.notes.append(note)

    plugin.write(sys.argv[-1])
except Exception as e:
    for i in traceback.format_exception(e.__class__, e, e.__traceback__):
        print(i, end='')
    os.system('pause')
