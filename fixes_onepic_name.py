# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 22:26:43 2022

@author: NBPub
"""


import sqlite3
from pathlib import Path
from tqdm import tqdm

con = sqlite3.connect('database.db') # name db
total = con.execute("SELECT COUNT(path) FROM Albums WHERE images = 1").fetchone()[0] # get total
query = "SELECT path FROM Albums WHERE images = 1" # get all albums that contain at least an image, previously ensured that only one pic per album
pics = ['.jpg','.jpeg','.gif','.png','.tif', '.tiff', '.webp', '.bmp'] # known image formats
names = ['cover','folder','front'] # acceptable cover art names for Navidrome, see "CoverArtPriority" (https://www.navidrome.org/docs/usage/configuration-options/)

# Initialize counters
success = 0
okay = 0
# Execute query within progress bar
pbar = tqdm(con.execute(query), total=total, unit='♥')

for path in pbar: # Iterate through
    pbar.set_postfix({str(success+okay):path[0]})
    for file in Path(path[0]).iterdir():
        if file.suffix in pics:
            if file.stem not in names:
                file.rename(Path(path[0],f'folder{file.suffix}')) # rename picture to be "folder.extension", if not in names listed above
                success += 1
            else:
                okay += 1

        
print('\n\n', 'changed:',success, 'already fine:', okay, '/', total, '\n\n', round((success+okay)*100/total,2),'%')
con.close()
     
