import glob
import os
phones = ['pau', 'br', 'exh', 'axh', 'cgh', 'vf', 'a', 'e', 'i', 'o', 'u', 'aa', 'ao', 'au', 'oa', 'ax', 'eh', 'uu', 'uo', 'ui', 'eu', 'oe', 'er', 'ih', 'uh', 'an', 'en', 'in', 'on', 'un', 'rn', 'p', 'b', 'bv', 'ts', 't', 'd', 'dd', 'dj', 'dg', 'jh', 'tg', 'c', 'k', 'g', 'gh', 's', 'z', 'zz', 'tz', 'dz', 'ch', 'sh', 'zh', 'f', 'v', 'h', 'x', 'th', 'dh', 'n', 'nj', 'ny', 'gn', 'm', 'ng', 'w', 'j', 'y', 'll', 'gl', 'lh', 'r', 'rr', 'rh', 'rx', 'rw', 'l', 'kx', 'q']

for file in glob.glob('*.lab'):
    with open(file) as f:
        i = f.readline()
        line_count = 1
        while i:
            p = i.strip().split()
            i = f.readline()
            if p[-1] not in phones:
                print(f'In {file}: {p[-1]} is not in the list. At line {line_count}')

            if int(p[0]) == int(p[1]):
                print(f'In {file}: {p[-1]} has the same start and end. At line {line_count}')
            line_count += 1

os.system('pause')
