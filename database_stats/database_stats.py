import os
import glob
import pyutau
import sys
import time
import traceback
from argparse import ArgumentParser

notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def midi_to_note(x):
    octave = x // 12 - 1
    note = x % 12
    return notes[note] + str(octave)

def midi_to_hz(x):
    return 440 * (2 ** ((x - 69) / 12))

try:
    parser = ArgumentParser(description='Calculates some statistics for your existing NNSVS database')
    parser.add_argument('db', help="The database's folder location")
    parser.add_argument('--all-labs', '-L', action='store_true', help="Include all LABs in the LAB pass.")
    parser.add_argument('--include-pau', '-P', action='store_true', help="Include pau phoneme in the phoneme tally passes.")

    args, _ = parser.parse_known_args()
    db = args.db
    
    print('Finding all USTs . . . ')
    usts = glob.glob(db + '/**/*.ust', recursive=True)

    print('Finding corresponding LABs . . . ')
    labs = []
    if not args.all_labs:
        for i in usts:
            _, file = os.path.split(i)
            fname, _ = os.path.splitext(file)
            labs.extend(glob.glob(db + f'/**/{fname}.lab', recursive=True))
    else:
        labs = glob.glob(db + '/**/*.lab', recursive=True)

    print('Caching LABs . . . ')
    phones = []
    for i in labs:
        temp = []
        with open(i) as f:
            for j in f.readlines():
                temp.append(j.strip().split()[-1])
        phones.append(temp)

    print('Tallying phonemes . . . ')
    mono_dens = {}
    for i in phones:
        for p in i:
            if p != 'pau' or args.include_pau:
                try:
                    mono_dens[p] += 1
                except KeyError:
                    mono_dens[p] = 1

    mono_dens = dict(sorted(mono_dens.items(), key=lambda x : x[1], reverse=True))

    print('Tallying diphones . . . ')
    diph_dens = {}
    for i in phones:
        N = len(i)
        for j in range(0, N-2):
            k = i[j] + ' ' + i[j+1]
            if (i[j] != 'pau' and i[j+1] != 'pau') or args.include_pau:
                try:
                    diph_dens[k] += 1
                except KeyError:
                    diph_dens[k] = 1

    diph_dens = dict(sorted(diph_dens.items(), key=lambda x : x[1], reverse=True))
    
    print('Tallying notes . . . ')
    note_dens = {}
    note_count = 0
    for i in usts:
        ust = pyutau.UtauPlugin(i)
        del ust.notes[-1]
        for note in ust.notes:
            if note.lyric not in ['R', 'pau']:
                note_count += 1
                try:
                    note_dens[note.note_num] += note.length
                except KeyError:
                    note_dens[note.note_num] = note.length

    print('Calculating things idk . . . ')
    note_dens = dict(sorted(note_dens.items(), reverse=True))
    total_note = sum(note_dens.values())
    mean_note = 0
    for k, v in note_dens.items():
        mean_note += k * v
    mean_note /= total_note

    print('Writing out stats in a text file . . . ')
    note_range = list(note_dens.keys())
    lo_range = midi_to_note(note_range[-1])
    hi_range = midi_to_note(note_range[0])
    lo_hz = midi_to_hz(note_range[-1])
    hi_hz = midi_to_hz(note_range[0])
    closest_note = midi_to_note(int(round(mean_note)))
    mean_hz = midi_to_hz(mean_note)
    
    with open(db + '/stats.txt', 'w') as f:
        f.write(f'Overall Range: {lo_range} ~ {hi_range} ({lo_hz:.3f} ~ {hi_hz:.3f})\n')
        f.write(f'Note Count: {note_count}\n')
        f.write(f'Total Note Length (UTAU length): {total_note}\n')
        f.write(f'Average Pitch: {mean_hz:.3f} Hz (~{closest_note})\n\n')
        
        f.write(f'Note Density (based on UTAU length now YAY)\n')
        for k, v in note_dens.items():
            f.write(f'{midi_to_note(k)}: {v}\n')

        f.write(f'\nMonophone Density\n')
        for k, v in mono_dens.items():
            f.write(f'{k}: {v}\n')

        f.write(f'\nDiphone Density\n')
        for k, v in diph_dens.items():
            f.write(f'{k}: {v}\n')
    
except Exception as e:
    for i in traceback.format_exception(e.__class__, e, e.__traceback__):
        print(i, end='')

_ = input('Press enter to continue . . . ')
