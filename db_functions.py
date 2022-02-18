# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 13:37:30 2022

@author: NBPub
"""

# Import libraries
from pathlib import Path
from datetime import datetime
import re
from mutagen.oggvorbis import OggVorbis
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3
from mutagen.easymp4 import EasyMP4
import stat
from tqdm import tqdm

def tally(con):
    # Delete defunct exceptions
    with con:
        con.execute("DELETE FROM Exceptions \
                     WHERE path NOT IN (SELECT path FROM Albums)")    
    
    # Albums, Tracks count for Artists table
    albums = con.execute("SELECT COUNT(artist), artist FROM Albums GROUP BY artist;").fetchall()
    con.executemany("UPDATE Artists SET albums=? WHERE name=?", albums)    
    tracks = con.execute("SELECT COUNT(artist), artist FROM Tracks GROUP BY artist;").fetchall()
    con.executemany("UPDATE Artists SET tracks=? WHERE name=?", tracks) 
    con.commit()
    del albums, tracks
    
    # Total track size for Albums, Artists tables
    albumsquery = "SELECT round(sum(filesize),2), Tracks.album \
                   FROM Tracks \
                       INNER JOIN ALBUMS \
                   ON Tracks.artist = Albums.artist and Tracks.album = Albums.album_name \
                       GROUP BY Tracks.artist,Tracks.album"
    
    artistsquery = "SELECT round(sum(filesize),2), Tracks.artist\
                   FROM Tracks \
                       INNER JOIN ALBUMS \
                   ON Tracks.artist = Albums.artist and Tracks.album = Albums.album_name \
                       GROUP BY Tracks.artist"
    
    artists = con.execute(artistsquery).fetchall()
    con.executemany("UPDATE Artists SET size=? WHERE name =?", artists)
    albums = con.execute(albumsquery).fetchall()    
    con.executemany("UPDATE Albums SET size=? WHERE album_name =?", albums)
    con.commit()
    del artists,albums

def make_tables(con):
    con.execute('DROP TABLE IF EXISTS Artists;')
    con.execute('DROP TABLE IF EXISTS Albums;')
    con.execute('DROP TABLE IF EXISTS Tracks;')
    con.execute('DROP TABLE IF EXISTS Errors;')
    # con.execute('DROP TABLE IF EXISTS Exceptions;')

    # Artists Table
    con.execute('''CREATE TABLE Artists
                (name TEXT PRIMARY KEY, path TEXT NOT NULL, albums INTEGER, 
                 tracks INTEGER, size INTEGER, other TEXT, modified TEXT NOT NULL)''')
    # Albums Table
    con.execute('''CREATE TABLE Albums
                (album_name TEXT, artist TEXT, tracks INTEGER, year TEXT, format TEXT,
                 images INTEGER, hidden INTEGER, subfolders TEXT, other TEXT, 
                 size INTEGER, path TEXT NOT NULL,
                 FOREIGN KEY (artist) REFERENCES Artists (name))''')
    # Songs Table
    #  modified TEXT NOT NULL,
    con.execute('''CREATE TABLE Tracks
                (artist TEXT, album TEXT, filename TEXT NOT NULL, tagname TEXT, 
                 tracknum TEXT, discnum TEXT, tagartist TEXT, tagalbum TEXT, tagyear TEXT,
                 tagalbumartist TEXT, composer TEXT, genre TEXT,
                 tagcomment INTEGER, filesize INTEGER, path TEXT NOT NULL,
                 FOREIGN KEY (album) REFERENCES Albums (album_name)
                 FOREIGN KEY (artist) REFERENCES Artists (name))''')     
                
    # Errors Table
    con.execute('''CREATE TABLE Errors
                (artist TEXT, album TEXT, errors INTEGER, tracks INTEGER, 
                 FOREIGN KEY (album) REFERENCES Albums (album_name)
                 FOREIGN KEY (artist) REFERENCES Artists (name))''') 
                
    Exceptions Table
    con.execute('''CREATE TABLE IF NOT EXISTS Exceptions
                (artist TEXT, album TEXT, type TEXT, path TEXT,
                 FOREIGN KEY (album) REFERENCES Albums (album_name)
                 FOREIGN KEY (artist) REFERENCES Artists (name))''')                 
                
    con.commit()
    
# Data for Artists: Name, Path, Date Modified   
def artists_dir(con, folder):   
    start = []
    for val in folder.iterdir():
        if val.is_dir():
            name = Path(val).name
            mod = datetime.fromtimestamp(val.stat().st_mtime).isoformat(timespec='milliseconds')
            start.append((name, str(val), mod))
    
    # remove special folders from scan (Syncthing, foobar2000 playlists
    [start.remove(item) for item in start if item[0] == '.stfolder' or item[0] == 'Playlists']    
    # Add to Artists Table
    con.executemany("INSERT INTO Artists (name,path,modified) VALUES (?,?,?)", start)
    con.commit()

# Data for Albums: name, year, format
# Data for Artists: singles, other files + images  
def albums_dir(con, tunes, pics):
    pattern = re.compile(r'(?P<album>.+) \((?P<year>.+)\) \[(?P<format>.+)\]', re.IGNORECASE)
    selection = "SELECT path FROM Artists" # get row id to add test limits
    sql = "INSERT INTO Albums (album_name,artist,year,format,path) VALUES (?,?,?,?,?)"

    for row in con.execute(selection):
        for child in Path(row[0]).iterdir():
            if child.is_dir(): 
                # could capture regex errors
                album_re = re.search(pattern, Path(child).name)
                album_name = album_re.group('album')
                album_format = album_re.group('format')
                album_year = album_re.group('year')
                
                # sub-album check, tracks == 0 sufficient for now
                extensions = [val.suffix for val in sorted(child.iterdir())]
                tracks = sum([ext in tunes for ext in extensions])
                if tracks == 0:
                    entry = []
                    for subalbum in child.iterdir():
                        # could check isdir
                        entry.append((f'{album_name} {subalbum.name}', Path(row[0]).name,\
                                      album_year, album_format, str(subalbum)))
                    con.executemany(sql,entry)
                else:
                    entry = (album_name, Path(row[0]).name, album_year, album_format, str(child))
                    con.execute(sql, entry)
            else: # other stuff in folder
                exists =  con.execute("SELECT other,name FROM Artists WHERE path = (?)", (row[0],)).fetchone()
                # current info in artist table [singles, other, name]
                other = exists[0]
                if other:
                    other = f'{other},{Path(child).suffix}'
                else:
                    other = Path(child).suffix                            
                con.execute("UPDATE Artists SET other=? WHERE name=?", (other, exists[1]))
    con.commit()
    
    
# Data for Albums: tracks, images, other
# Data for Tracks: all of it    
def tracks_dir(con, tunes, pics, spec):

    if spec:
        selection = ('SELECT artist,album_name,path FROM Albums WHERE name=?',(spec,))
    else:
        selection = "SELECT artist,album_name,path FROM Albums"  # get row id to add test limits
    
    total = con.execute("SELECT count(rowid) from Albums").fetchone()[0] # Make part of selection!
    

    album_entry = []    
    pbar = tqdm(con.execute(selection), total=total, unit='alb')
    for row in pbar:
        pbar.set_postfix({row[0]:row[1]}) # artist-album display for progress bar
      
      # can get rowid in selection, then do a numerical limit to scan
      # if row[3] > limit:
        #     break
            # return row[3]
          
        entryd = {"tracks":0,"images":0,"hidden":0,"subfolder":'',"other":''} # initialize entry into Albums table
        tagdata = [] # initialize list, dictionaries of tag data for each track in an album
        err = 0 # initialize error reporting
        
        for val in Path(row[2]).iterdir(): # Iterate through album directories
            # If file is a song, get the tag data for entry into the Tracks table, capture errors and continue
            if val.suffix in tunes: 
                entryd["tracks"] += 1
                try:
                    if val.suffix == '.mp3':
                        data = dict(EasyID3(val)) # can delay converting to dictionary if making any modifications to the file
                        f = ID3(val) # Deep tag read for comment or picture 
                                         
                        # Tag Picture
                        # data["picture"] = 1 if "APIC:" in f else 0
                        # Tag Comment
                        data["comment"] = 1 if any(s.startswith('COMM') for s in f) else 0
                        del f                       
                        
                        # Delete useless keys, other examples: 'COMM:iTunes_CDDB', 'TXXX:BUYCDURL'
                        # for s in keys:
                        #     if s.startswith('PRIV:'):
                        #         del f[s]
                        #         f.save()                           
                    
                    # MP4 and OGG files, ignore comments for now. NULL in comments field will be convenient way to select these files in future
                    elif val.suffix == '.m4a':
                        data = dict(EasyMP4(val))
                        data["comment"] = None if "comment" not in data else data["comment"]
                       
                    elif val.suffix == '.ogg':
                        data = dict(OggVorbis(val))
                        data["comment"] = None if "comment" not in data else data["comment"]
                   
                    data["path"] = str(val)
                    tagdata.append(data)
                    
                except:
                    err += 1
            # If file isn't a song, note if it's an image, subfolder, or other. A list of extensions is saved for "other" files.
            elif val.suffix.lower() in pics:
                if bool(val.stat().st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN):
                    entryd["hidden"] += 1
                else:
                    entryd["images"] += 1
            elif val.is_dir():
                if entryd["subfolder"] == '':
                    entryd["subfolder"] = val.name
                else:
                    entryd["subfolder"] = f'{entryd["subfolder"]},{val.name}'            
            else:
                if entryd["other"] == '':
                    entryd["other"] = val.suffix
                else:
                    entryd["other"] = f'{entryd["other"]},{val.suffix}' 
        for key in entryd:
            if entryd[key] == 0 or entryd[key] == '':
                entryd[key] = None
        
        # Populate list, will be saved to Albums table at end
        album_entry.append((entryd["tracks"], entryd["images"], entryd["hidden"], entryd["subfolder"], entryd["other"], row[2]))
        
        track_entries = []        
        for tag in tagdata:  
            path = tag["path"]
            # mod = datetime.fromtimestamp(Path(path).stat().st_mtime).isoformat(timespec='milliseconds')
            filesize = round(Path(path).stat().st_size/1048576,2)
            filename = Path(path).stem
            
            tagname = tag["title"][0] if 'title' in tag else None
            tracknum = tag["tracknumber"][0] if 'tracknumber' in tag else None
            discnum = tag["discnumber"][0] if 'discnumber' in tag else None
            tagartist = tag["artist"][0] if 'artist' in tag else None
            tagalbum = tag["album"][0] if 'album' in tag else None
            tagyear = tag["date"][0] if 'date' in tag else None
            tagalbumartist = tag["albumartist"][0] if 'albumartist' in tag else None
            composer = tag["composer"][0] if 'composer' in tag else None
            genre = tag["genre"][0] if 'genre' in tag else None
            
            track_entries.append((row[0], row[1], filename, tagname, tracknum,
                                  discnum, tagartist, tagalbum, tagyear,
                                  tagalbumartist, composer, genre,
                                  tag["comment"],filesize, path))
        
        # Save to Tracks table
        sql = "INSERT INTO Tracks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        con.executemany(sql, track_entries)
        
        # Save to Errors table
        if err > 0:
            con.execute("INSERT INTO Errors Values (?,?,?,?)", (row[0],row[1], err, entryd["tracks"]))
    # Save to Albums table    
    con.executemany("UPDATE Albums SET tracks=?, images=?, hidden=?, subfolders=?, other=? WHERE path=?", album_entry)
    con.commit()
