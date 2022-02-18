# -*- coding: utf-8 -*-
"""
Created on Mon Jan 31 13:57:23 2022

@author: NBPub
"""

import sqlite3
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import json
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4
import pandas as pd
from tqdm import tqdm

# establish connection
con = sqlite3.connect('database.db') 

# get total number for progress bar
total = con.execute("SELECT COUNT(Tracks.path) \
                    FROM Tracks \
                    INNER JOIN Albums \
                    	ON Tracks.album = Albums.album_name AND Tracks.artist = Albums.artist \
                    WHERE length(tagyear) > 4").fetchone()[0]

# Join Tracks and Albums tables by their common columns (specify both artist and album, as album names are not unique)
# Get rows where tagyear is not XXXX, ex: "01-02-1969" vs "1969"
# could also specify length(tagyear) <> 4
query = "SELECT Tracks.artist, album_name, year, tagyear, Tracks.path \
        FROM Tracks \
        INNER JOIN Albums \
        	ON Tracks.album = Albums.album_name AND Tracks.artist = Albums.artist \
        WHERE length(tagyear) > 4"
                    
# Last.FM API, see link in ReadMe
# Add your info here to use
headers = {'user-agent': '<your-application-name>'}
base = 'http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key=<YOUR KEY HERE>'
                    
success = 0
mismatch = 0
table = pd.DataFrame(columns = ['Year', 'last.fm', 'Tagged'])

pbar = tqdm(con.execute(query), total=total, unit='tag')
for art, alb, year, tagyear, path  in pbar:
    pbar.set_postfix({art:path})
    path = Path(path) # change from path from string to object
    
    if str(year) == tagyear[0:4]: # change year tags if tag and folder agree
        if path.suffix == '.mp3':
            f = EasyID3(path)
            f['date'] = str(year)
            f.save()
        elif path.suffix == '.m4a':
            f = EasyMP4(path)
            f['date'] = str(year)
            f.save()
        success += 1
    else: # save to table if they don't agree, will review further
        mismatch += 1
        ind = '-'.join([art,alb])
        if ind in table.index:
            if tagyear != table.loc[ind, 'Tagged']:
                table.loc[ind, 'Tagged'] = f'{table.loc[ind,"Tagged"]}, {tagyear}'
        else:
            table.loc[ind,'Year'] = year
            table.loc[ind,'Tagged'] = tagyear
            try: # get release year from last.fm page
                URL = f'{base}&artist={art.replace(" ","+")}&album={alb.replace(" ","+")}&format=json'
                data = json.loads(requests.get(URL,headers=headers).content)['album']['url']
                page = requests.get(data)
                soup = BeautifulSoup(page.content,'html.parser')
                a = set(soup.find_all('dt', class_= 'catalogue-metadata-heading'))
                
                for element in a:
                    if element.contents[0] == 'Release Date':
                        table.loc[ind,'last.fm'] = element.next_sibling.next_sibling.contents[0]
                    
                        
            except:
                table.loc[ind,'last.fm'] = '<>' # indicates failed lookup
                        
if table.shape[0] > 1: # save table as HTML file, add basic results above table
    table = table.to_html()
    preamble = f'<h1> Successful</h1>  <h2 style="color:green;">{success}/{total} for {round(success/total,2)*100}%</h2> \
                 <h1> Mismatches</h1> <h2 style="color:red;"> {mismatch} for {round(mismatch/total,2)*100}%</h2> <br />'             
    with open('TagYearFixes.html', 'w', encoding='utf-8') as report:
        report.write(' '.join([preamble,table]))
        
else: # No mismatches to review, then just print results
    print('\n\n',round(success/total,2)*100, '  fixed',success,'out of', total)
    print()

con.close()
