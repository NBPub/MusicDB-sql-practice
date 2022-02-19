# -*- coding: utf-8 -*-
"""
Created on Tue Feb  1 15:27:11 2022

@author: NBPub
"""

import pandas as pd
from pathlib import Path
from tqdm import tqdm
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4

# Table generated from fixes_year_format.py
table = pd.read_html('TagYearFixes.html', index_col=0)[0]
table["last.fm"] = table["last.fm"].fillna(0).astype(int) # styling adjustments
table["Result"] = table["Result"].fillna('failed lookup')

# Manual Fixes, gotta look stuff up to adjust, can save print or save these
# table[table.Result == 'failed lookup']
# table[table.Result == '<>']

# Script Fix
# perform when last.FM confirms either Folder or song Tag has correct year
# errors captured and printed at end, ex: weird characters, see Sigur Ros
fix = table[(table.Result == 'Folder') | (table.Result == 'Tag')]
# Intialize counters, error capturer
retagged = 0
renamed = 0
err = ''
# Iterate through table with progress bar
pbar = tqdm(enumerate(fix.Path), total = fix.shape[0], unit = '♥')
for i,path in pbar:
    pbar.set_postfix({fix.Result[i]:fix.index[i]})

    try:
        if fix.iloc[i,3] == 'Folder': # Retag all songs if Folder correct, could check if tag is correct before changing to reduce modifications
            for song in Path(path).iterdir():
                if song.suffix == '.mp3':
                    f = EasyID3(song)
                    f['date'] = str(fix.iloc[i,2])
                    f.save()
                    retagged +=1
                elif song.suffix == '.m4a':
                    f = EasyMP4(song)
                    f['date'] = str(fix.iloc[i,2])
                    f.save()
                    retagged +=1
        elif fix.iloc[i,3] == 'Tag': # Rename folder if Tag correct
            year_pos = path.rindex(fix.iloc[i,0])
            newpath = Path(''.join([path[0:year_pos],str(fix.iloc[i,2]),path[year_pos+4:]]))
            Path(path).rename(newpath)
            renamed += 1
    except Exception as e: # Capture error, print at end
        err = ''.join([err,'\n',str(e)])
        
print('\n\n', 'Retagged: ', retagged, '\nRenamed: ', renamed)
print('Failures:')
print(err)

