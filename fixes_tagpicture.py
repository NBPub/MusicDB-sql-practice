# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 15:17:31 2022

@author: NBPub
"""

import sqlite3
from pathlib import Path
from tqdm import tqdm
from mutagen.id3 import ID3
from mutagen.mp4 import MP4


# Pass 1: Tracks with embedded picture, no cover art in folder --> extract one picture into folder
# Pass 2: Tracks with embedded picture, cover art in folder --> delete all embedded pictures

con = sqlite3.connect('database.db') # name db

# total for progress bar, see query note below
total = con.execute("SELECT COUNT(Tracks.path) \
                    FROM Tracks \
                    INNER JOIN Albums \
                    	ON Tracks.album = Albums.album_name AND Tracks.artist = Albums.artist \
                    WHERE tagpicture = 1 AND images IS NOT NULL").fetchone()[0]

# This is Pass 2, for Pass 1 images should be NULL
query = "SELECT DISTINCT Albums.path, Albums.artist, album_name \
        FROM Tracks \
        INNER JOIN Albums \
        	ON Tracks.album = Albums.album_name AND Tracks.artist = Albums.artist \
        WHERE tagpicture = 1 AND images IS NOT NULL"


success = 0
failed = 0
count = 0

# Pass 1
# Add folder picture from first tag picture
pbar = tqdm(con.execute(query), total=total, unit='♥')
for p, art, alb in pbar:
    pbar.set_postfix({art:alb})   
    subquery = "SELECT path FROM Tracks WHERE artist = ? AND album = ? AND tagpicture = 1" # get tracks with pictures, should define this outside of loop
    track = Path(con.execute(subquery, (art,alb)).fetchone()[0]) # choose first one to extract image
    
    try:
        f = ID3(track)["APIC:"] # image as bytes
        extension = f.mime.lstrip('image/') # get extension from string, to save appropriately
        extension = 'folder.jpg' if extension == 'jpeg' else f'folder.{extension}' # name image "folder.<proper extension>", rename jpeg to jpg because that's annoying
        with open(Path(Path(p), extension), 'wb') as file: # save image in album folder
            file.write(f.data)
        success += 1
    except:
        print('Failed: ',art,alb)
        failed += 1

print('\n\n', total, '\n worked: ', success, 'failed: ', failed)
con.close()

# Pass 2
# Delete all pictures
pbar = tqdm(con.execute(query), total=total, unit='♥')
for p, art, alb in pbar:
    pbar.set_postfix({art:alb})
    count += 1
    
    subquery = "SELECT path FROM Tracks WHERE artist = ? AND album = ? AND tagpicture = 1" # again, should define this outside of loop
    tracks = con.execute(subquery, (art,alb))
    
    for track in tracks:
        track = Path(track[0])
        try:
            f = ID3(track)
            del f["APIC:"]
            f.save()
            success += 1
        except:
            print('Failed: ',art,alb)
            failed += 1

print('\n\n', count, '\n worked: ', success, 'failed: ', failed)
con.close()



    
        
    




