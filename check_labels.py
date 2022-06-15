import glob
import os
phones = ['br', 'a', 'i', 'u', 'e', 'o', 'N', 'cl', 't', 'd', 's', 'sh', 'j', 'z', 'ts', 'k', 'kw', 'g', 'gw', 'h', 'b', 'p', 'f', 'ch', 'ry', 'ky', 'py', 'dy', 'ty', 'ny', 'hy', 'my', 'gy', 'by', 'n', 'm', 'r', 'w', 'v', 'y', 'pau', 'Edge']

density = {}

for i in phones:
    density[i] = 0

for file in glob.glob('*.lab'):
    with open(file) as f:
        i = f.readline()
        line_count = 1
        while i:
            p = i.strip().split()
            i = f.readline()
            if p[-1] not in phones:
                print(f'In {file}: {p[-1]} is not in the list. At line {line_count}')
            else:
                density[p[-1]] += 1

            if int(p[0]) == int(p[1]):
                print(f'In {file}: {p[-1]} has the same start and end. At line {line_count}')

            line_count += 1

for k, v in density.items():
    if v == 0:
        print(f'No data for {k}')

os.system('pause')
