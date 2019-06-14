"""
`cd data/mutlinli`
`wget http://www.nyu.edu/projects/bowman/multinli/multinli_1.0.zip`
`unzip multinli_1.0.zip`
`mv multinli_1.0/* .`

`cd ../../data/xnli`
`wget https://www.nyu.edu/projects/bowman/xnli/XNLI-1.0.zip`
`unzip XNLI-1.0.zip`
`mv XNLI-1.0/* .`
`split xnli.dev.jsonl xnli.dev. -a 1 -l 2490`
`split xnli.test.jsonl xnli.test. -a 1 -l 5010`
`python rename_files.py`
"""

import os

langs = ['ar', 'bg', 'de', 'el', 'en', 'es', 'fr', 'hi', 'ru', 'sw', 'th', 'tr', 'ur', 'vi', 'zh']

old_filenames_dev = ['xnli.dev.' + c for c in 'abcdefghijklmno']
old_filenames_test = ['xnli.test.' + c for c in 'abcdefghijklmno']

new_filenames_dev = ['xnli.dev.' + c for c in langs]
new_filenames_test = ['xnli.test.' + c for c in langs]

old = old_filenames_dev + old_filenames_test
new = new_filenames_dev + new_filenames_test

mapping = dict() 
for o, n in zip(old, new):
    mapping[o] = n
    
for filename in os.listdir('.'):
    if filename in mapping:
        new_filename = mapping[filename]
        os.rename(filename, new_filename)