# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 12:04:09 2022

@author: NBPub
"""

# Import libraries
import sqlite3
from pathlib import Path
import time
from contextlib import redirect_stdout

# Import functions, see db_functions.py
from db_functions import make_tables, artists_dir, albums_dir, tracks_dir, tally

# Establish timer
class Timer:
    def __enter__(self):
        self.start = time.time()
        return self
    def __exit__(self, *args):
        elapsed = time.time()-self.start
        print('Finished in {:.2f} seconds \n\n'.format(elapsed)) 


# Establish file extensions
tunes = ['.mp3','.ogg', '.m4a'] # FLAC in different libary, ignoring my one WMA song
pics = ['.jpg','.jpeg','.gif','.png','.tif', '.tiff', '.webp', '.bmp'] # known image formats within directory

# Establish connection, can play with PRAGMA modes to optimize speed
con = sqlite3.connect('database.db') # name db
music_folder = Path('X:/Music/') # point to music


with open(f'{time.asctime().replace(":","•")}-optional-description-here.txt', 'w', encoding='utf-8') as f: # text file notes durations for DB creation
    with redirect_stdout(f):
        with Timer() as t:
            # Make tables, delete and remake if exists
            make_tables(con)
            
            # Music Folders - Artists
            artists_dir(con, music_folder)
            print('Tables made and Artists filled')
              
        with Timer() as t:
            # Artist Folders - Albums+
            albums_dir(con, tunes, pics)
            count1 = con.execute("SELECT count(rowid) from Albums").fetchone()[0]
            count2 = con.execute("SELECT count(name) from Artists").fetchone()[0]
            print(f'{count1} albums for {count2} artists.')
        
        
        with Timer() as t:
            # Album Folders - Tracks+
            tracks_dir(con, tunes, pics, None) # pass list of albums for limited run
            count1 = con.execute("SELECT count(rowid) from Albums where tracks IS NOT NULL").fetchone()[0]
            count2 = con.execute("SELECT count(artist) from Tracks").fetchone()[0]
            print(f'{count2} tracks for {count1} albums')
        
        with Timer() as t:
            # Data for Artists: number of albums and tracks
            # Final iteration, sum song file sizes
            tally(con)
            print('Artist tallies for tracks and albums')
        
        con.close()
