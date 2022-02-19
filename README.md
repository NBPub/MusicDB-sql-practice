# MusicDB-sql-practice
Collection of python scripts used to evaluate + fix music collection. 

Switching to a tag-based music player, from one based on directory structure, provided motivation to clean up my library. So I used the process to learn Python's [SQLite](https://docs.python.org/3/library/sqlite3.html#) module. Conveniently, a nice SQLite [tutorial site](https://www.sqlitetutorial.net/) uses a music library as an example. I used [DB Browser for SQLite](https://sqlitebrowser.org/) to browse the database and craft queries. [last.fm](last.fm) was used as a check for album release years and to fill missing cover art. Their [API](https://www.last.fm/api/show/album.getInfo) does not provide release date, as indicated, so I had to scrape album pages for release year.

## Packages Utilized:
* [python](https://www.python.org/) **3.8.12**
* [mutagen](https://mutagen.readthedocs.io/en/latest/) **1.45.1**  - read/modify tags, *note: collection only contained MP3, MP4, and OGG files*
* [tqdm](https://tqdm.github.io/) **4.62.3** - progress bars make everything better
* [rich](https://rich.readthedocs.io/en/stable/introduction.html) **10.16.2**- colors make things better, too
* [pywin32](https://pypi.org/project/pywin32/) - needed to adjust file attributes, such as unhiding.
* [requests](https://docs.python-requests.org/en/latest/) **2.27.1** - consume APIs or get HTML content for scraping
* [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/) **4.10.0** - scrape [last.fm](last.fm) album pages due to failure of API
* [pandas](https://pandas.pydata.org/) **1.3.5** - for some reporting outputs. Python's [CSV](https://docs.python.org/3/library/csv.html) could be used instead.

*Prior work: Ensure all album folder names follow format `<ALBUM-NAME> (<YEAR>) [<Format>]`*

# Part One - DB Creation
`db_creation.py` and `db_functions.py` serve to create the SQLite database. A timer and progress bar provide live monitoring and records of scan times. For my library, initial scans took 6-8 minutes, and subsequent scans (not the first of the day) took 1-2 minutes. Various junk is left as comments in `db_functions.py`, as this is the best way to check/apply changes to all files or folders. For example, embedded ID3 pictures were first identified, secondly deleted, and thirdly ignored, over the days of scanning / fixing.

My music folder is organized by artist. An artist folder contains album folders or single tracks (and potentially other hidden files). Album folders can contain tracks, images, and other files. These folders and files were used to populate 3 SQLite tables: **Artists**, **Albums**, and **Tracks**.

The **Artists** table contains the following columns:
* Name (TEXT, PRIMARY KEY)
* Path (TEXT)
* Albums (INTEGER)
* Tracks (INTEGER)
* Size (INTEGER)
* Other (TEXT)
* Modified (TEXT)

Initially I captured the date modified of the folders so I could scan for recent changes and then update the database accordingly. However, I found it was fast enough to simply re-scan the entire directory after making changes. Details for the other tables can be inferred from the code. During the scan, an **Errors** table was used to capture any problem areas. An **Exceptions** table was also added to improve the tag-fixing process. This table is persisted through re-scans, whereas the others are deleted and recreated.


# Part Two - Various Fixes

Fixes are saved as individual scripts*, varying in complexity, to facilitate changes I wanted to make. See `fixes_artistTag.py` for the most complex example. They follow a basic structure of:

1) Identify certain problem
2) Execute SQLite query to gather problem-children
3) Iterate through children and: **Fix** / **Ignore** - save with entry into **Exceptions** table / **Flag** - HTML or CSV table saved for later referral

The fix step is the main thing that varies. For more complex fixes (user-decisions needed), I provided simple options to speed up the process. Some scripts utilize [Rich](https://rich.readthedocs.io/en/stable/introduction.html) to improve readability. Note, I used all of these with [Spyder](https://www.spyder-ide.org/), and therefore a very limited set of Rich's features.

\*Two of the files have multiple parts (run it one way first, another way next). These are described in the comments.

## File Descriptions

See the python files and their comments for more details. Comments in files low on the following table may be less descriptive, if the same process was described in a file higher up on the table..

| fixes_ | Problem | Notes |
| :----: | --- | --- |
| `year_format.py` | Tag date not in XXXX format | If tagged year and year in folder agree, fix file and save. If not, save to separate file and check last.fm for data |
| `year_mismatch.py` | Tag date and Folder date do not agree | Uses file from above. Retags files or renames folder depening on which one last.fm confirms |
| `year_NullFill.py` | No Tag date for song | Adds tag date based on folder year (all have been checked from above step) |
| `tagpicture.py` | I don't want embedded images in files | Delete all tracks with picture in tag, if folder lacks picture, then save the first one in the folder. |
| `nopic.py` | No Cover Art | Use Artist/Album to get picture from last.fm, if not found save info with link for [wikipedia](https://en.wikipedia.org/wiki/Main_Page) search to separate file |
| `hiddenpic.py` | Hidden image files, Cover Art already there. Empty image files leftover from previous script fix. | Various iterations to keep file and delete rest, based on file size |
| `albumartist_VA to folder.py` | Tag album artist is some form of "Various Artists" | Switch it to the artist indicated by Folder |
| `AlbArt-VA.py` | Tag Artist and Folder Artist disagree, no Tag album artist | For each album print tagged artist(s) and folder artist, provide various fixing **options** for user. |
| `albumTag.py` | Tag Album and Folder Album disagree | Print tag vs folder info, provide various fixing **options** for user. |
| `artistTag.py` | Tag Artist OR Tag Album Artist doesn't match Folder artist | For each album print tagged artist(s) and folder artist, provide various fixing **options** for user. This one allows selection of multiple options. |

## Other
`db_timer_example.txt` shows the TXT file output from `db_creation.py`, a sample database is not provided.

I included `info_MP4_tags.py` to show how to scan through an MP4 (.m4a file) collection. Unlike standardized [ID3 tags](https://id3.org/id3v2.3.0#Declared_ID3v2_frames), there is no convention for these files to follow. To get an idea of what can be modified outside of Mutagen's EasyMP4 module, you can run this over known MP4 files and see:

* Unique tags within files for each folder
* Total occurences of each tag

I used this to figure out how to access the embedded pictures and the song's comments.
