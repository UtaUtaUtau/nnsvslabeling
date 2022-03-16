import sys
import os
import traceback

floc = sys.argv[-1]
base, ext = os.path.splitext(floc)

def groups(iterable, num):
    for i in range(0, len(iterable) - num + 1):
        res = []
        for j in range(0, num):
            res.append(iterable[i + j])
        yield tuple(res)

try:
    if ext == '.lab':
        lab = open(floc).readlines()
        with open(base + '.txt', 'w') as f:
            for i in lab:
                time = i.strip().split()
                if '.' in time[0]:
                    f.write('\t'.join(time) + '\n')
                else:
                    f.write(f'{float(time[0]) / (10 ** 7):.6f}\t{float(time[1]) / (10 ** 7):.6f}\t{time[2]}\n')
    elif ext == '.txt':
        aud = open(floc).readlines()
        for i in range(len(aud) - 1, -1, -1):
            if aud[i].startswith('\\'):
                del aud[i]
                
        with open(base + '.lab', 'w') as f:
            for i, j in groups(aud, 2):
                time1 = i.strip().split()
                time2 = j.strip().split()
                f.write(f'{int(float(time1[0]) * (10 ** 7))} {int(float(time2[0]) * (10 ** 7))} {time1[2]}\n')
            if not aud[-1].strip().endswith('-'):
                time = aud[-1].strip().split()
                f.write(f'{int(float(time[0]) * (10 ** 7))} {int(float(time[1]) * (10 ** 7))} {time[2]}\n')
except Exception as e:
    for err in traceback.format_exception(e.__class__, e, e.__traceback__):
        print(err, end='')
    if e.__class__.__name__ == 'IndexError':
        print('Probably a label without a phoneme in it? Here:\n')
        print(i)
        print('Search it in the audacity or HTS mono label you put in.')
    os.system('pause')
