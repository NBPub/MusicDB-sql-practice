# -*- coding: utf-8 -*-
"""
Created on Thu Feb  3 17:17:30 2022

@author: NBPub
"""

import sqlite3
from pathlib import Path
from mutagen.mp4 import MP4
from mutagen.easymp4 import EasyMP4
import pandas as pd
from tqdm import tqdm

con = sqlite3.connect('database.db') # name db
total = con.execute("SELECT COUNT(path) FROM Tracks WHERE tagcomment IS NULL").fetchone()[0]
query = "SELECT artist,album,path FROM Tracks WHERE tagcomment IS NULL" # see db_functions.py for why this selects (almost) only MP4 files

folders = pd.DataFrame(columns = ["Keys"])
output = pd.DataFrame(columns = ["Occurences"])
pbar = tqdm(con.execute(query), total=total, unit='♥')

other = [] # in case the query does not only return MP4 files
deletes = 0
skips = 0

for art,alb, file in pbar:
    pbar.set_postfix({art:alb})
    p = Path(file)
    ind = f'{art}-{alb}'
    folders.loc[ind, "Keys"] = []
    
    if p.suffix != '.m4a':
        if ind not in other:
            other.append(ind)
    else:
        song = MP4(p)          
        for key in song:
            if key in output.index:
                output.loc[key,"Occurences"] += 1
            else:
                output.loc[key,"Occurences"] = 1
                
            if key not in folders.loc[ind, "Keys"]:
                folders.loc[ind, "Keys"].append(key)
        # example: if you identify a tag you want to delete
        # if 'covr' in song:
            # del song['covr']
            # song.save()
            # deletes += 1
        # else:
            # skips += 1                

output.to_html('MP4 - Occurences.html')
folders.to_html('MP4 - Folders.html')        
