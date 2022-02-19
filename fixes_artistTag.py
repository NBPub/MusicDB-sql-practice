# -*- coding: utf-8 -*-
"""
Created on Thu Feb 10 13:55:01 2022

@author: NBPub
"""

import sqlite3
from pathlib import Path

from mutagen.oggvorbis import OggVorbis
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4
import pandas as pd
from rich import print

con = sqlite3.connect('database.db') # name db

# First Run: Artist != (tagartist and albumartist), make sure at least one matches or exception

# Second Run: Artist != (tagartist or albumartist), should just be albums with mix of artists
# ~~NOTE~~ need to add parantheses in WHERE part of sql statement for second run
# Album Artist should be green. For other mismatches fix/del albumartist

total = con.execute("SELECT COUNT(DISTINCT Albums.path)\
                    FROM Albums \
                    INNER JOIN Tracks \
                    	ON Tracks.album = Albums.album_name AND Tracks.artist = Albums.artist \
                    WHERE (Tracks.tagartist <> Tracks.artist OR Tracks.tagalbumartist <> Tracks.artist) \
                        AND Albums.path NOT IN (SELECT path FROM Exceptions WHERE type LIKE 'Artist %')").fetchone()[0]
                                           
                     
query = "SELECT DISTINCT album_name, Albums.artist, Albums.path \
        FROM Tracks \
        INNER JOIN Albums \
        	ON Tracks.album = Albums.album_name AND Tracks.artist = Albums.artist \
        WHERE (Tracks.tagartist <> Tracks.artist OR Tracks.tagalbumartist <> Tracks.artist) \
            AND Albums.path NOT IN (SELECT path FROM Exceptions WHERE type LIKE 'Artist %')"

subquery = "SELECT DISTINCT tagartist, tagalbumartist FROM Tracks WHERE artist = ? AND album = ?"


artreview = pd.DataFrame(columns = ['Artist','Album','TagArtist(s)', 'TagAlbArt(s)'])
renames = {}
count = 0
options = {0: "Exit", 1:"Del Album Artist", 2:"Change Folder Name", 3: "Flag Folder", \
           4: "Change Both Tags", 5:"Change Artist", 6: "Change Album Artist", \
           77: "Exception to DB: Artist Mix",
           7: "Exception to DB: Artist DirChar", 8: "Exception to DB: Artist AKA-Info",
           9: "Skip Entry"}

# Options 4-6 will take another input for what to change to
# Options 7-8 will take another input for Exception type
subchoice456 = {4: ["artist","albumartist"], 5:["artist"], 6:["albumartist"]}
subchoice78 = {7: "Artist DirChar", 8: "Artist Info-AKA", 77: "Artist Mix"}

# Here potential actions are defined as functions
# This will allow multiple options to be selected and performed

def option1(path): # Delete AlbumArtist tag
    for file in Path(path).iterdir():
        try:
            if file.suffix == '.mp3':
                song = EasyID3(file)
                del song["albumartist"]
                song.save()                
            elif file.suffix == '.m4a':
                song = EasyMP4(file)
                del song["albumartist"]
                song.save()                
            elif file.suffix.lower() == '.ogg':
                song = OggVorbis(file)
                del song["albumartist"]
                song.save()
        except Exception as e:
            print(f'[magenta italic]{file.name}: {str(e)}[/]')
            
    print("\n[cyan italic]AlbumArtist tags deleted[/]\n")

def option2(path,art, to): # Rename Artist Folder (queue until done)   
    ArtFolder = str(Path(path).parent)
    Rename = ArtFolder.replace(art,to)
    renames[ArtFolder] = Rename
    
    print("\n[cyan italic]Rename added to queue[/]\n")
    
def option3(path, art, alb, tagartists, tagalbumartists): # Flag Folder for review
    artreview.loc[path, "Artist"] = art
    artreview.loc[path, "Album"] = alb
    artreview.loc[path, "TagArtist(s)"] = tagartists
    artreview.loc[path, "TagAlbArt(s)"] = tagalbumartists
    
    print("\n[cyan italic]Folder flagged[/]\n")
    
def option456(path, art, choice): # Change both tags
    retag = subchoice456[choice]
    for file in Path(path).iterdir():
        if file.suffix == '.mp3':
            song = EasyID3(file)
            for tag in retag:
                song[tag] = art
            song.save()                
        elif file.suffix == '.m4a':
            song = EasyMP4(file)
            for tag in retag:
                song[tag] = art
            song.save()                
        elif file.suffix.lower() == '.ogg':
            song = OggVorbis(file)
            for tag in retag:
                song[tag] = art
            song.save()
            
    print("\n[cyan italic]Tags adjusted[/]\n")

def option78(path, art, alb, choice):
    entry = (art, alb, subchoice78[choice], path)
    sql = "INSERT INTO Exceptions VALUES (?,?,?,?)"
    with con:
        con.execute(sql, entry)    
    
    print("\n[cyan italic]DB Exception added[/]\n")
    
# Iterate through query:
# print relevant info, present options, perform actions

for alb, art, path in con.execute(query):
    fetch = con.execute(subquery,(art,alb)).fetchall()
    tagartists = set([val[0] for val in fetch])
    tagalbumartists = set([val[1] for val in fetch])
    
    count += 1
    print(count,'/',total, ' ▀▄▀▄ ', round(count*100/total,2),'% \n')
    print(f'[on violet]Album: {alb}[/] \n')
    print(f'[underline]Artist:[/]\n[bold]{art}[/]')
    print('═══───═══')
    print(f'[violet underline]TagArtist(s)[/] [{len(tagartists)}]:')
    for tag in tagartists:
        if tag == art:
            print(f'[bold green]{tag}[/]')
        else:
            print(f'[bold red]{tag}[/]')
    print('═══───═══')
    if len(tagalbumartists) > 0:
        print(f'[violet underline]AlbumArtist(s)[/][{len(tagartists)}]:')
        for tag in tagalbumartists:
            if tag == art:
                print(f'[bold green]{tag}[/]')
            else:
                print(f'[bold red]{tag}[/]') 
    else:
        print('[cyan on green]No Album Artist tag[/]')
    
    
    print('\n')     
    for key in options:
        print(f'{key} - {options[key]}')
    choices = [int(val) for val in input("Select action to take: ").split(',')]
    out = False
    
    for choice in choices:
        if choice == 0:
            out = True
            break
        elif choice == 1:
            option1(path)
        elif choice == 2:
            to = str(input("Enter new name: "))
            option2(path,art,to)
        elif choice == 3:
            option3(path,art,alb,tagartists, tagalbumartists)
        elif choice > 3 and choice < 7:
            option456(path,art,choice)
        elif choice > 6 and choice < 9 or choice == 77:
            option78(path,art,alb,choice)
        elif choice == 9:
            break
        else:
            print("\n[magenta]Invalid option, continuing . . .[/]\n")
   
  # need to break twice to Exit due to nesting        
    if out: 
        break
    else:
        continue
        
con.close() # Close connection

# Attempt renames, print out failures
for key in renames:
    try:
        Path(key).rename(renames[key])
        print(f'[green]{key} to {renames[key]}[/]')
    except:
        print(f'[red]ERROR:[/] {key} to {renames[key]}')

# HTML file for flag folder review
if artreview.shape[0] > 0:
    artreview.to_html('artreview.html')
    
