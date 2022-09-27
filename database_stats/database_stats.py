import os
import glob
import pyutau
import sys
import time
import traceback
import csv
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
    parser.add_argument('--all-labs', '-l', action='store_true', help="Include all LABs in the LAB pass.")
    parser.add_argument('--include-pau', '-p', action='store_true', help="Include pau phoneme in the phoneme tally passes.")
    parser.add_argument('--skip-diphone', '-s', action='store_true', help="Skip diphone density in calculations.")
    parser.add_argument('--write-diphone', '-w', action='store_true', help="Include diphone density in the .csv version.")

    args, _ = parser.parse_known_args()
    db = args.db
    calc_diphone = not args.skip_diphone
    
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

    print('Reading LABs . . . ')
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

    if calc_diphone:
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
    note_dens_length = {}
    note_dens_presence = {}
    note_count = 0
    for i in usts:
        ust = pyutau.UtauPlugin(i)
        del ust.notes[-1]
        for note in ust.notes:
            if note.lyric not in ['R', 'pau']:
                note_count += 1
                try:
                    note_dens_length[note.note_num] += note.length
                except KeyError:
                    note_dens_length[note.note_num] = note.length

                try:
                    note_dens_presence[note.note_num] += 1
                except KeyError:
                    note_dens_presence[note.note_num] = 1

    print('Calculating things idk . . . ')
    note_dens_length = dict(sorted(note_dens_length.items(), reverse=True))
    note_dens_presence = dict(sorted(note_dens_presence.items(), reverse=True))
    total_note_length = sum(note_dens_length.values())
    mean_note = 0
    for k, v in note_dens_length.items():
        mean_note += k * v
    mean_note /= total_note_length

    note_range = list(note_dens_length.keys())
    lo_range = midi_to_note(note_range[-1])
    hi_range = midi_to_note(note_range[0])
    lo_hz = midi_to_hz(note_range[-1])
    hi_hz = midi_to_hz(note_range[0])
    closest_note = midi_to_note(int(round(mean_note)))
    mean_hz = midi_to_hz(mean_note)

    basic_info = {
            'Overall Range' : f'{lo_range} ~ {hi_range} ({lo_hz:.3f} ~ {hi_hz:.3f})',
            'Note Count' : note_count,
            'Total Note Length (UTAU length)' : total_note_length,
            'Average Pitch' : f'{mean_hz:.3f} Hz (~{closest_note})'
        }

    print('Writing out stats in a text file . . . ')
    with open(db + '/stats.txt', 'w') as f:
        for k, v in basic_info.items():
            f.write(f'{k}: {str(v)}\n')

        f.write(f'\nNote Density (based on note length)\n')
        for k, v in note_dens_length.items():
            f.write(f'{midi_to_note(k)}: {v}\n')

        f.write(f'\nNote Density (based on note presence)\n')
        for k, v in note_dens_presence.items():
            f.write(f'{midi_to_note(k)}: {v}\n')

        f.write(f'\nMonophone Density\n')
        for k, v in mono_dens.items():
            f.write(f'{k}: {v}\n')

        if calc_diphone:
            f.write(f'\nDiphone Density\n')
            for k, v in diph_dens.items():
                f.write(f'{k}: {v}\n')

    print('Writing out stats in a .csv file . . . ')
    header = ['Note', 'Density (lengths)', 'Density (presence)', '', 'Phoneme', 'Density', '', '', '']

    if calc_diphone and args.write_diphone:
        header = header[:7] + ['Diphone', 'Density', ''] + header[7:]

    cols = len(header)
    rows = max(len(note_dens_length), len(mono_dens)) + 1

    if calc_diphone and args.write_diphone:
        rows = max(len(note_dens_length), len(mono_dens), len(diph_dens)) + 1

    sheet = [['' for c in range(cols)] for r in range(rows)]

    sheet[0] = header
    for r in range(1, rows):
        i = r - 1
        if i < len(note_dens_length):
            dens_len = list(note_dens_length.items())[i]
            dens_pres = list(note_dens_presence.values())[i]
            sheet[r][0] = midi_to_note(dens_len[0])
            sheet[r][1] = dens_len[1]
            sheet[r][2] = dens_pres

        if i < len(mono_dens):
            dens = list(mono_dens.items())[i]
            sheet[r][4] = dens[0]
            sheet[r][5] = dens[1]

        if calc_diphone and args.write_diphone:
            if i < len(diph_dens):
                dens = list(diph_dens.items())[i]
                sheet[r][7] = dens[0]
                sheet[r][8] = dens[1]

        if i < len(basic_info):
            info = list(basic_info.items())[i]
            sheet[r][-2] = info[0]
            sheet[r][-1] = info[1]

    with open(db + '/stats.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(sheet)
    
except Exception as e:
    for i in traceback.format_exception(e.__class__, e, e.__traceback__):
        print(i, end='')

_ = input('Press enter to continue . . . ')
