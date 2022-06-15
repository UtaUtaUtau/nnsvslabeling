# nnsvslabeling
Python scripts I made to make NNSVS labeling easier.

# How to Use
### General
You will need Python for all of these to work, of course. I wrote this in Python 3.7.

### lab2audacity.py
This script can convert between Audacity labels (in .txt filetype) and HTS mono labels (in .lab filetype). Drag and drop the file over the script file and it will do the conversion. It cannot batch convert labels.

This script automatically connects the ends of each label to the start of the next label. If the label ends with `-`, it will exclude it in the HTS label.

This script does not do anything about timing with HTS mono labels.

### check_labels.py

It's exactly what the file says. It checks for wrong phonemes in every .lab file that it finds. It also checks if you have a label that has the same start and end timing. To run, put it in the folder where you keep your .lab files and just, run normally!

It checks Japanese labels by default, but if you want to change what language it checks, just open it up and change the `phones` list to the phoneme list you want it to be.

Update 06/15/2022: Added a feature that counts how many instances of each phoneme is present in the labels. The program will alert you if there is no instance of a certain phoneme by default but you may change it to be a certain threshold. At line 28 in the code (looks like `if v == 0:`) you may change it to something like `if v <= n:` with `n` being a threshold that you think is appropriate enough.

### lab2ust
The whole lab2ust folder will be put in the UTAU plugins folder.

Just follow the steps that the plugin gives you. It supports stringing together phonemes to notes. It supports the Japanese phoneme set that NNSVS, CeVIO, Sinsy, NEUTRINO, and Synthesizer V uses.

Japanese is coded in differently to support suffixes on vowels. This was mostly an idea that my friends and I thought of. In that case, Japanese hopefully supports `VS` where `V` is the vowel and `S` is the suffix. (e.g. falsetto could be `aF`, `iF`, and so on)

It also supports ARPAbet and X-Sampa for other languages, but stringing CCs is a bit primitive, and it only cuts them at the middle.

It will always separate the phonemes `sil`, `pau`, `cl`, `br`, `vf`, and `Edge`.

This will only directly translate timing according to the BPM of the UST. It puts all notes at middle C (C4).

Update 09/28/2021: lab2ust now quantizes notes. You need to specify the note length of the quantization though. Here's a list of note lengths for quantization. If you don't want quantization, just put 1.

Update 03/02/2022: lab2ust can now read `.frqs` to automatically place the pitches of the notes. It is recommended to generate `.frqs` with moresampler for highest accuracy. PS: It can ONLY read `.frqs` so you would need to convert the `.mrq` to `.frq`. This can be done with frq editor. If you are OK with checking the frequencies instead, you can generate with speedwagon instead.

| Quantize | Note Length |
| --- | --- |
| 128th note | 15 |
| 64th triplet | 20 |
| 64th note | 30 |
| 32nd triplet | 40 |
| 32nd note | 60 |
| 16th triplet | 80 |
| 16th note | 120 |
| 8th triplet | 160 |
| 8th note | 240 |
| Quarter triplet | 320 |
| Quarter note | 480 |
