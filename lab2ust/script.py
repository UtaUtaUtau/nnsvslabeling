import pyutau
import traceback
import time
import sys
import os
import math
import struct
import json

def quantize(x, intensity):
    return int(round(x / intensity)) * intensity

def hz_to_midi(x):
    x = max(x, 55)
    note = 12 * (math.log2(x / 440))
    return int(round(note + 69))

#Copied from https://github.com/titinko/frq0003gen/blob/master/src/frq0003gen.cpp
def base_frq(f0, f0_min=55, f0_max=1760):
    value = 0
    r = 1
    p = [0, 0, 0, 0, 0, 0]
    q = 0
    avg_frq = 0
    base_value = 0
    
    for i in range(len(f0)):
        value = f0[i]
        if value < f0_max and value > f0_min:
            r = 1

            for j in range(6):
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

try:
    plugin = pyutau.UtauPlugin(sys.argv[-1])
    lab = open(input('Drag and drop the .lab file here: ').strip('"')).readlines()
    phonemes = []
    duration = []
    pitches = []
    ups = 480 * float(plugin.settings['Tempo']) / 60
    pps = 44100 / 256

    frq_loc = input('Drag and drop the .frq file here (leave blank if no frq): ').strip('"')
    frq = [0]
    
    #Save phonemes in duration in list. Convert durations to note lengths
    for i in lab:
        ph = i.strip().split()
        phonemes.append(ph[2])
        duration.append(ups * (float(ph[1]) - float(ph[0])) / (10 ** 7))

    #Load in frequency file if it's inputted
    if frq_loc:
        print('Reading .frq file...')
        with open(frq_loc, 'rb') as f:
            header_text = f.read(8).decode('utf-8')
            assert header_text == 'FREQ0003'

            samples_per_frq = struct.unpack('<i', f.read(4))[0]
            assert samples_per_frq == 256

            f.read(24)

            num_chunks = struct.unpack('<i', f.read(4))[0]

            for i in range(num_chunks):
                curr = struct.unpack('<2d', f.read(16))[0]
                if curr <= 55:
                    frq.append(frq[-1])
                else:
                    frq.append(curr)
        del frq[0]
        
    #Ask if the label is Japanese or not.
    jpn = input('Is this label for Japanese? [y/n] ')
    if jpn.lower() == 'y':
        jpn = True
    else:
        jpn = False
        
    fuse = input('Automatically fuse? [y/n] ')
    if fuse.lower() == 'y':
        if jpn:
        #Fuse CVs
            vowels = ['a', 'i', 'u', 'e', 'o', 'A', 'I', 'U', 'E', 'O']
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
            standalone = ['pau', 'br', 'sil']
            langs = json.loads(open(os.path.dirname(sys.argv[-2]) + '/languages.json').read())
            print('Select phoneme set')
            for k, v in enumerate(langs):
                print(f'{k+1}: {v["name"]}')
            phoneme_mode = int(input()) - 1
            vowels = langs[phoneme_mode]["vowels"]
            phoneme_ranges = []
            duration_ranges = []
            i = 0
            #Get ranges hopefully
            while i < len(phonemes):
                if phonemes[i] in standalone: # Standalones are standalones for a reason <3
                    phoneme_ranges.append((i, i))
                    duration_ranges.append((i, i))
                else:
                    if phonemes[i] in vowels: # Vowels need to find their onset and coda so yah
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
                    else: # If the consonants are surrounded by standalones they're just a consonant island so they're fused in one note !
                        vowel_near_left = True
                        vowel_near_right = True
                        s = 0
                        e = 0
                        for j in range(i-1, -1, -1):
                            if phonemes[j] in standalone:
                                vowel_near_left = False
                                s = j+1
                                break
                            if phonemes[j] in vowels:
                                break

                        for j in range(i+1, len(phonemes)):
                            if phonemes[j] in standalone:
                                vowel_near_right = False
                                e = j-1
                                break
                            if phonemes[j] in vowels:
                                break

                        if not vowel_near_left and not vowel_near_right:
                            phoneme_ranges.append((s, e))
                            duration_ranges.append((s, e))
                            i = e
                i += 1

            #Correct duration ranges
            for i in range(len(duration_ranges) - 1):
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

    #Make pitch list
    if frq_loc:
        start = 0
        for i in range(len(duration)):
            end = start + duration[i] / ups
            i_start = int(round(start * pps))
            i_end = int(round(end * pps))
            pitch = hz_to_midi(base_frq(frq[i_start:i_end]))
            pitches.append(pitch)
            start = end
    else:
        pitches = [60 for x in range(len(duration))]
    
    #Compensate duration for decimal to integer
    for i in range(len(duration) - 1):
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

    quant_strength = input('Quantization in note length (int) [60]: ')
    if not quant_strength:
        quant_strength = 60
    else:
        quant_strength = int(quant_strength)
        
    #Compensate for quantization
    for i in range(0, len(duration) - 1):
        quant_dur = quantize(duration[i], quant_strength)
        error = duration[i] - quant_dur
        duration[i] = quant_dur
        duration[i+1] += error

    duration[-1] = quantize(duration[-1], quant_strength)
    
    for i in range(0, len(duration)):
        note = pyutau.create_note(phonemes[i] if phonemes[i] not in ['pau', 'sil'] else 'R', duration[i], note_num = pitches[i])
        if note.lyric == 'R':
            note.note_num = 60
        plugin.notes.append(note)

    plugin.write(sys.argv[-1])
except Exception as e:
    for i in traceback.format_exception(e.__class__, e, e.__traceback__):
        print(i, end='')
    os.system('pause')
