# -*- coding: utf-8 -*-
"""
Created on Tue Feb  8 14:13:44 2022

@author: NBPub
"""

import sqlite3
from pathlib import Path

from mutagen.oggvorbis import OggVorbis
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4
import pandas as pd

con = sqlite3.connect('database.db') # name db

total = con.execute("SELECT COUNT(DISTINCT Albums.path)\
                    FROM Albums \
                    INNER JOIN Tracks \
                    	ON Tracks.album = Albums.album_name AND Tracks.artist = Albums.artist \
                    WHERE Tracks.tagartist <> Tracks.artist \
                        AND Tracks.tagalbumartist IS NULL \
                        AND Albums.path NOT IN (SELECT path FROM Exceptions WHERE type LIKE 'Artist %')").fetchone()[0]

# Albums in which songs have no album artist tagged, and a mismatch of Folder and tagged artist
# Ignore albums with an Artist type Exception
query = "SELECT DISTINCT Albums.artist, album_name, Albums.path \
        FROM Tracks \
        INNER JOIN Albums \
        	ON Tracks.album = Albums.album_name AND Tracks.artist = Albums.artist \
        WHERE Tracks.tagartist <> Tracks.artist \
            AND Tracks.tagalbumartist IS NULL \
            AND Albums.path NOT IN (SELECT path FROM Exceptions WHERE type LIKE 'Artist %')"

# Get list of tagged artists for songs in a certain album
subquery = "SELECT DISTINCT(tagartist) FROM Tracks WHERE artist = ? AND album = ?"

# Intializations
artreview = pd.DataFrame(columns = ['Artist','Album','TagArtist(s)']) # output table
renames = {} # dictionary of folders to be renamed, perform at end
count = 0

# Various actions a user can choose to take while iterating through albums
options = {0: "Exit", 1:"Change tag to Artist", 2:"Add Album Artist", 3: "Skip", \
           4: "Flag folder", 5:"Exception to DB: Artists DirChar", \
           6:"Exception to DB: Artists Info-AKA", 7: "Change Folder name to Tag"}
    
for art, alb, path in con.execute(query):
    # Tagged Artists for songs in album
    fetch = con.execute(subquery,(art,alb)).fetchall()
    tagartists = [val[0] for val in fetch]
    
    # Header: Print progress for sanity
    # Print pertinent info
    count += 1
    print(count,'/',total, ' ▀▄▀▄ ', round(count*100/total,2),'% \n')
    print('Album:', alb,'\n')
    print(f'Artist vs TagArtist(s)[{len(tagartists)}]: \n\n{art}')
    print('═══───═══')
    if len(tagartists) > 1:
        for tag in tagartists: print(f'{tag}')
    else:
        print(tagartists[0])
    
    print('\n')
    # print options, take input
    for key in options:
        print(f'{key} - {options[key]}')
    choice = int(input("Select action to take: "))
    
    # take appropriate actions
    if choice not in options:
        print("Invalid option, skipping entry")   
        continue
    elif choice == 0: # Exit
        break
    elif choice == 3: # Skip
        continue
    elif choice == 4: # Flag folder
        artreview.loc[path, "Artist"] = art
        artreview.loc[path, "Album"] = alb
        artreview.loc[path, "TagArtist(s)"] = tagartists   
    
    elif choice == 5: # Exception to DB, DirChar
        entry = (art, alb, 'Artist DirChar', path)
        sql = "INSERT INTO Exceptions VALUES (?,?,?,?)"
        with con:
            con.execute(sql, entry)
    
    elif choice == 6: # Exception to DB, Temp (to be deleted later)
        entry = (art, alb, 'Artist Info-AKA', path)
        sql = "INSERT INTO Exceptions VALUES (?,?,?,?)"
        with con:
            con.execute(sql, entry)
    
    elif choice == 7: # Change folder name          
        ArtFolder = str(Path(path).parent)
        Rename = ArtFolder.replace(art,tagartists[0])
        renames[ArtFolder] = Rename
       
    
    else: # Change / Add Tag
        if choice == 1:
            rename = ["artist",art]
        elif choice == 2:
            rename = ["albumartist",art]
            
        for file in Path(path).iterdir():
            if file.suffix == '.mp3':
                song = EasyID3(file)
                song[rename[0]] = rename[1]
                song.save()                
            elif file.suffix == '.m4a':
                song = EasyMP4(file)
                song[rename[0]] = rename[1]
                song.save()                
            elif file.suffix.lower() == '.ogg':
                song = OggVorbis(file)
                song[rename[0]] = rename[1]
                song.save()           
    
con.close()

# renames
for key in renames:
    Path(key).rename(renames[key])
    print(key, 'to', renames[key])

# output table as HTML
if artreview.shape[0] > 0:
    artreview.to_html('artreview.html')
