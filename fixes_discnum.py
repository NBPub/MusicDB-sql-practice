# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 20:03:52 2022

@author: NBPub
"""

import sqlite3
from pathlib import Path
from rich import print
import pandas as pd

from mutagen.oggvorbis import OggVorbis
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4

con = sqlite3.connect('database.db') # name db

# Function to adjust discnumber tag for song(s)
def DiscChanger(paths, action):
    for track in paths:
        track = Path(track)
        if track.suffix == '.mp3':
            file = EasyID3(track)
        elif track.suffix == '.m4a':
            file = EasyMP4(track)
        elif track.suffix == '.ogg':
            file = OggVorbis(track)
            
        if file: # Limit saves for changes
            if "discnumber" not in file or file["discnumber"][0] != str(action):
                file["discnumber"] = str(action)
                file.save()

# Get all Tracks that contain discnumber tag, will filter more during iteration
query = "SELECT DISTINCT artist, album FROM Tracks WHERE discnum IS NOT NULL \
    AND (artist,album) not in (SELECT artist,album FROM Exceptions WHERE type = 'Temp MultiDisc')"
total = con.execute("SELECT COUNT(DISTINCT album) FROM Tracks WHERE discnum IS NOT NULL \
                    AND (artist,album) not in (SELECT artist,album FROM Exceptions WHERE type = 'Temp MultiDisc')").fetchone()[0]

# For a given album, get all the discnumber and tracknumber tags
subquery = "SELECT discnum, tracknum, tagname, path FROM Tracks WHERE artist = ? AND album = ?"

# Initializations
review = pd.DataFrame(columns = ['Artist','Album','Note'])
count = 0
options = {0: "Exit", 1:"Set all to 1", 2:"Set all discNums to", 3: "Adjust tracks", \
           4: "Skip + DB Exception", 5: "Flag for review", 7: "Power Skip"}

for art,alb in con.execute(query):
    count += 1
    tracklist = con.execute(subquery,(art,alb)).fetchall() # discnum, tracknum, name, path
    disclist = set(val[0] for val in tracklist)
    if len(disclist) > 1: # Skip if album only contains one tagged discnumber
        print(count,'/',total, ' ▀▄▀▄ ', round(count*100/total,2),'% \n')
        print(f'[on blue underline]Tracklist for {art}-{alb}:[/] \n')
        lister = 0
        for song in tracklist:
            lister += 1
            if lister < 10:
                printlister = f' {lister}'
            else:
                printlister = lister
            if song[0] == '0' or song[0] == None:
                print(f'{printlister}) [bold red]{song[0]}[/]:{song[1]} - {song[2]}')
            else:
                print(f'{printlister}) [black]{song[0]}[/]:{song[1]} - {song[2]}')
        
        print('\n')     
        for key in options:
            print(f'[magenta]{key}[/] - {options[key]}')
        choice = input("Select action to take: ")
        try:
            choice = int(choice)
        except:
            print('[red]Invalid option, continuing . . . [/] \n\n')
            continue
        
        if choice == 0: # Exit   
            print('[green]Peace![/] \n\n')
            break
        elif choice == 7: # Power Skip
            continue
        
        elif choice == 4: # Skip + Exception
            path = con.execute("SELECT path FROM Albums WHERE artist = ? and album_name = ?", (art,alb)).fetchone()[0]
            entry = (art, alb, 'Temp MultiDisc', path)
            sql = "INSERT INTO Exceptions VALUES (?,?,?,?)"
            with con:
                con.execute(sql, entry)             
            print('[green]Skip! temp exception added[/] \n\n')
            continue
        
        elif choice == 5: # Flag for review
            note = input('add note?: ')
            review.loc[count, "Artist"] = art
            review.loc[count, "Album"] = alb
            if note != '':
                review.loc[count, "Note"] = note
            
        elif choice == 1: # Change all to 1
            paths = [val[3] for val in tracklist]
            DiscChanger(paths,1)
            print('[green]Disc One to rule them all![/] \n\n')
            
        elif choice == 2: # Change all to X
            action = int(input("New Discnumber: "))
            paths = [val[3] for val in tracklist]
            DiscChanger(paths,action)
            print('[green]Disc numbers changed[/] \n\n')
            
        elif choice == 3: # Change some to X
            action = int(input("New Discnumber: "))
            trackselect = input("Track(s) to change. dash for range, comma for individuals: ")
            try:
                if '-' in trackselect:
                    low = int(trackselect.split('-')[0])-1
                    hi = int(trackselect.split('-')[1])
                    paths = [val[3] for val in tracklist[low:hi]]
                else:
                    selection = [int(val)-1 for val in trackselect.split(',')]
                    paths = [tracklist[val][3] for val in selection]
                DiscChanger(paths,action)
                print('[green]Disc numbers changed[/] \n\n')
            except Exception as e:
                print(f'[red]{str(e)}[/] \n\n')
        else:
            print('[red]Invalid option, continuing . . . [/] \n\n')

con.close()

if review.shape[0] > 0:
    review.to_csv('disc-track-numbers.csv')
    review.to_html('disc-track-numbers.html')
     
