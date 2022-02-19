# -*- coding: utf-8 -*-
"""
Created on Thu Feb  3 12:04:15 2022

@author: NBPub
"""

import sqlite3
from pathlib import Path
import win32con, win32api
from tqdm import tqdm
import stat

# Another two parter

# Pass 1, cover art exists in folder
# Scans and keeps 1 image
# From hidden > 0, folder images NOT NULL

con = sqlite3.connect('database.db')
total = con.execute("SELECT COUNT(path) FROM Albums WHERE hidden IS NOT NULL AND images IS NOT NULL").fetchone()[0]
query = "SELECT artist, album_name, path FROM Albums WHERE hidden IS NOT NULL AND images IS NOT NULL"
pics = ['.jpg','.jpeg','.gif','.png','.tif', '.tiff', '.webp', '.bmp'] # image formats
names = ['cover','folder','front'] # image names accepted by music player

renamed = 0
unhidden = 0
deleted = 0

pbar = tqdm(con.execute(query), total=total, unit='♥')

for art, alb, path in pbar:
    pbar.set_postfix({art:alb})
    
    # Gather all images, including hidden
    art = []
    for file in Path(path).iterdir():
        if file.suffix in pics:
            d = {"path": file, "size": file.stat().st_size}
            art.append(d)
    
    # If more than one image, keep only biggest file
    ordered = sorted(art, key = lambda x: x['size'], reverse=True) # sort images by descending file size
    for file in ordered[1:]:
        file["path"].unlink()
        deleted += 1
    check = ordered[0]["path"]

    # Rename leftover image, if needed
    if check.stem.lower() not in names:
        check = check.rename(Path(path,f'folder{check.suffix}'))
        renamed += 1
    
    # Unhide image, if hidden
    if bool(check.stat().st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN):
        win32api.SetFileAttributes(str(check),win32con.FILE_ATTRIBUTE_NORMAL)
        unhidden += 1
        
print('\n\n', 'deleted:',deleted, 'renamed:', renamed, 'unhidden:', unhidden, '\n\n', total)
con.close()
     

        
        
# Pass 2, no cover art in folder       
# Scans and keeps 1 image
# From hidden > 0, folder images NULL

con = sqlite3.connect('database.db') # name db
total = con.execute("SELECT COUNT(path) FROM Albums WHERE hidden IS NOT NULL AND images IS NULL").fetchone()[0]
query = "SELECT artist, album_name, path, hidden FROM Albums WHERE hidden IS NOT NULL AND images IS NULL"
pics = ['.jpg','.jpeg','.gif','.png','.tif', '.tiff', '.webp', '.bmp']
names = ['cover','folder','front']

renamed = 0
unhidden = 0
deleted = 0

pbar = tqdm(con.execute(query), total=total, unit='♥')

for art, alb, path, hidden in pbar:
    pbar.set_postfix({art:alb})
    
    # Gather images (hidden only with this query)
    art = []
    for file in Path(path).iterdir():
        if file.suffix in pics:
            d = {"path": file, "size": file.stat().st_size}
            art.append(d)
    
    # If more than one image, keep only biggest file
    if hidden > 1:
        ordered = sorted(art, key = lambda x: x['size'], reverse=True) # sort images by descending file size
        for file in ordered[1:]:
            file["path"].unlink()
            deleted += 1
        check = ordered[0]["path"]
    else:
        check = art[0]["path"]
        
    
    # Rename leftover image, if needed
    if check.stem.lower() not in names:
        check = check.rename(Path(path,f'folder{check.suffix}'))
        renamed += 1
    
    # Unhide, if statement shouldn't be necessary
    if bool(check.stat().st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN):
        win32api.SetFileAttributes(str(check),win32con.FILE_ATTRIBUTE_NORMAL)
        unhidden += 1

print('\n\n', 'deleted:',deleted, 'renamed:', renamed, 'unhidden:', unhidden, '\n\n', total)
con.close()        
