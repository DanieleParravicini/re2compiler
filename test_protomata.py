from re import error
from re2compiler import compile
import os
import urllib.request
import warnings

verbose = False
ok = 0
total = 0
path = "protomata.regex"
if not os.path.exists(path):
    with urllib.request.urlopen("https://raw.githubusercontent.com/tjt7a/AutomataZoo/master/Protomata/code/protomata.regex") as response:
        html = response.read()
        with open(path,'w') as f:
            f.write(html.decode('utf-8'))

with open(path) as f:
    for i,line in enumerate(f.readlines()):
        #remove \( and )\
        line = line[2:-3]
        if verbose:
            print(f'regex {i+1}',flush=True)
            warnings.simplefilter('once')
        try:
            code        = compile(data=line, no_postfix=False, no_prefix=False, O1=True)
            num_instr   = len(code.split("\n"))
            if num_instr<256:
                ok+=1
        except Exception as e:
            print(f'regex {i+1}', e)
        
        total+=1
        if verbose:
            warnings.resetwarnings()
            print(f'code length: {num_instr}')
print(f'{ok} out of {total} correctly compiled')