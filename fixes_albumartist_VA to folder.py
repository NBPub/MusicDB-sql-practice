# -*- coding: utf-8 -*-
"""
Created on Fri Feb  4 16:04:49 2022

@author: Nish
"""

import sqlite3
from pathlib import Path

from mutagen.oggvorbis import OggVorbis
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4

from tqdm import tqdm

con = sqlite3.connect('database.db') # name db


total = 100 # I was messing up the formatting when running this, so I just set it to the number I saw when querying outside of Python

# Songs with tagged Album Artist: Various Artists, Various, VA, Uknown Album
query = 'SELECT DISTINCT Tracks.path, Albums.artist, tagartist, tagalbumartist \
        FROM Tracks \
        INNER JOIN Albums \
        	ON Tracks.album = Albums.album_name AND Tracks.artist = Albums.artist \
        WHERE tagalbumartist IN ("Various Artists", "Various", "VA", "Unknown Album")'
    
    
pbar = tqdm(con.execute(query), total=total, unit='♥')
fixed = 0
notfixed = 0

for path, art, tagart, tagAA in pbar:
    pbar.set_postfix({art:path})
    p = Path(path)
    
    
    try: # load file, adjust album artist, save. can capture errors with more detail if needed.
        if p.suffix == '.mp3':
            f = EasyID3(p)
        elif p.suffix == '.m4a':
            f = EasyMP4(p)
        elif p.suffix == '.ogg':
            f = OggVorbis(p)
            
        f["albumartist"] = art
        f.save()
        fixed += 1
    except:
        notfixed += 1
        
con.close()
    
