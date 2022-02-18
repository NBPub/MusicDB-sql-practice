# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 13:55:06 2022

@author: NBPub
"""

import sqlite3
from pathlib import Path
from tqdm import tqdm
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4

con = sqlite3.connect('database.db') # name db

# total for progress bar
total = con.execute("SELECT COUNT(Tracks.path) \
                    FROM Tracks \
                    INNER JOIN Albums \
                    	ON Tracks.album = Albums.album_name AND Tracks.artist = Albums.artist \
                    WHERE Tracks.tagyear IS NULL  AND length(Albums.year) < 5").fetchone()[0]

# No date in song's tag
query = "SELECT year, tagyear, Tracks.path \
        FROM Tracks \
        INNER JOIN Albums \
        	ON Tracks.album = Albums.album_name AND Tracks.artist = Albums.artist \
        WHERE Tracks.tagyear IS NULL  AND length(Albums.year) < 5" # excepting ranges
        
        
pbar = tqdm(con.execute(query), total=total, unit='♥')
count = 0
for year, blank, path in pbar: # iterate through and set date, save
    count +=1
    pbar.set_postfix({str(count):path})
    song = Path(path)
    if song.suffix == '.mp3':
        f = EasyID3(song)
        f['date'] = year
        f.save()
    elif song.suffix == '.m4a':
        f = EasyMP4(song)
        f['date'] = year
        f.save()
    # don't need to adjust OGG files    
con.close()
