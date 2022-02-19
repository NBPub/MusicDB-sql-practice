# -*- coding: utf-8 -*-
"""
Created on Sat Feb  5 17:44:58 2022

@author: NBPub
"""

import sqlite3
from pathlib import Path

from mutagen.oggvorbis import OggVorbis
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4
import pandas as pd

tunes = ['.mp3','.ogg', '.m4a']
con = sqlite3.connect('database.db') # name db
# total for progress bar
total = con.execute("SELECT COUNT(DISTINCT Albums.path) \
                    FROM Tracks \
                    INNER JOIN Albums \
                    	ON Tracks.album = Albums.album_name AND Tracks.artist = Albums.artist \
                    WHERE Tracks.tagalbum <> Tracks.album \
                    AND Albums.path NOT IN (SELECT path FROM Exceptions WHERE type LIKE 'Album %')").fetchone()[0]

# Albums for which at least one track's tag album does not match folder name
# Ignore previously added Exceptions
query = "SELECT DISTINCT Albums.artist, album_name, tagalbum, Albums.path \
        FROM Tracks \
        INNER JOIN Albums \
        	ON Tracks.album = Albums.album_name AND Tracks.artist = Albums.artist \
        WHERE Tracks.tagalbum <> Tracks.album \
        AND Albums.path NOT IN (SELECT path FROM Exceptions WHERE type LIKE 'Album %')"       

# Initialize, Establish potentail actions
output = pd.DataFrame(columns = ['Artist','Album', 'TagAlbum', 'path'])
options = {0: "Exit", 1:"Change Album Tag", 2:"Exception-DirChar", 3:"Exception-Info", \
           4:"Change Folder (Tag)", 5:"Change Folder (Custom)", 6:"Flag Directory", \
           7: "Skip Entry"}
count = 0

for art, alb, tagalb, path in con.execute(query):
    count += 1
    print(f'\n\n\n{count} out of {total} ~ {round(100*count/total,2)}% \n')
    print(f'Artist: {art} \n\n')
    print(f'Folder:\n {alb}\nvs\nTag:\n {tagalb} \n\n')
    
    for key in options:
        print(f'{key} - {options[key]}')

    choice = int(input("Select action to take: "))
    
    if choice not in options:
        print("Invalid option, skipping entry")   
    elif choice == 0: # Exit
        break
    elif choice == 7: # Skip
        continue
    
    elif choice == 1: # Adjust Tags
        for file in Path(path).iterdir():
            if file.suffix in tunes:
                if file.suffix == tunes[0]:
                    song = EasyID3(file)
                elif file.suffix == tunes[1]:
                    song = OggVorbis(file)
                elif file.suffix == tunes[2]:
                    song = EasyMP4(file)
                    
                song["album"] = alb
                song.save()
    
        
    elif choice == 2: # Exception to DB - DirChar
        entry = (art, alb, 'Album DirChars', path)
        sql = "INSERT INTO Exceptions VALUES (?,?,?,?)"
        con.execute(sql, entry)
        
    elif choice == 3: # Exception to DB - Info
        entry = (art, alb, 'Album ExtraInfo', path)
        sql = "INSERT INTO Exceptions VALUES (?,?,?,?)"
        con.execute(sql, entry) 
        
    elif choice == 4: # Folder to Tag
        rename = Path(path.replace(alb,tagalb))
        Path(path).rename(rename)
    
    elif choice == 5: # Custom Folder Rename
        print('\n Enter new name: \n')
        rename_input = str(input())
        rename = Path(path.replace(alb,rename_input))
        Path(path).rename(rename)        
        
    elif choice == 6:
        output.loc[count, "Artist"] = art
        output.loc[count, "Album"] = alb
        output.loc[count, "TagAlbum"] = tagalb
        output.loc[count, "path"] = path


con.commit()
con.close()

if output.shape[0] > 0:
    output.to_html('Album DirCheck.html')
    
