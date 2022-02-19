# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 21:01:41 2022

@author: NBPub
"""

import sqlite3
from pathlib import Path
import requests
import urllib.parse
import json
import pandas as pd
from tqdm import tqdm

con = sqlite3.connect('database.db') # name db
total = con.execute("SELECT COUNT(path) FROM Albums WHERE images IS NULL").fetchone()[0] # total for pbar
query = "SELECT artist, album_name, path FROM Albums WHERE images IS NULL" #  album folders without image

# try last.fm
# if not, populate table with art/alb/path/link to wiki search

# output table
output = pd.DataFrame(columns = ['path', 'wiki-search'])

# Last.FM API, see link in ReadMe, Add your info here to use
headers = {'user-agent': '<your-application-name>'}
base = 'http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key=<YOUR KEY HERE>'

# add parameter to wikibase and the link will be a search for that parameter
wikibase = 'https://en.wikipedia.org/w/index.php?search='

success = 0
pbar = tqdm(con.execute(query), total=total, unit='♥')
for art, alb, path  in pbar:
    pbar.set_postfix({art:alb})    
    URL = f'{base}&artist={urllib.parse.quote(art)}&album={urllib.parse.quote(alb)}&format=json'
    
    try:
        im = json.loads(requests.get(URL,headers=headers).content)['album']['image'][2]['#text'] # byte data for pic
        im_path = Path(path, 'folder.webp') # save image with name = folder, last.fm provides images in webp format
        with open(im_path, 'wb') as file:
            file.write(requests.get(im).content)
        success += 1
    except:
        output.loc[f'{art}-{alb}', 'path'] = path # path is nice to have when saving found pictures
        output.loc[f'{art}-{alb}', 'wiki-search'] = f'{wikibase}{urllib.parse.quote(alb)}'
        
print('\n\n', success, '/', total, '\n\n', output.shape[0], 'failed.')
output.to_html('NoPic-NoFM.html', render_links = True)
con.close()
        
    
