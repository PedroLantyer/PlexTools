import pathlib
import json
import pandas as pd
import ast
from typing import Literal, cast
from functools import cmp_to_key
from plexapi.playlist import Playlist
from plexapi.audio import Track
from plexapi.video import Video
from plexapi.server import PlexServer
from music import Track_Data
from movie import Movie_Data
from json_utils import get_json_save_path
from sorting_utils import get_sort_mode

class Playlist_Data:
    title: str
    id: int
    addedAt: str # ISO 8601 Datetime String
    pos: int # Position in the original playlist list

    def __init__(self, playlist: Playlist, pos: int):
        self.title = playlist.title
        self.id = playlist.ratingKey
        self.addedAt = playlist.addedAt.isoformat()
        self.pos = pos

    def print_playlist_data(self):
        print(f"Title: {self.title} | ID: {self.id} | Added At: {self.addedAt}")

def get_target_playlist_id(playlists: list[Playlist]):
    print("Playlists available:")
    for pl in playlists:
        print(pl.title)
    print("\n")

    while True:
            selected_playlist_title = input("Insert Target Playlist Title: ").strip().lower()
            match = [pl for pl in playlists if pl.title.lower()==selected_playlist_title]
            if not match:
                print("Playlist not found", end="\n\n")
            else:
                return match[0].ratingKey

def remove_duplicate_playlists(playlists: list[Playlist], data_for_playlists: list[Playlist_Data]):
    # FIND DUPES
    df = pd.DataFrame([vars(playlist) for playlist in data_for_playlists])
    df = df[df.duplicated(subset=["title"], keep=False)]

    if not len(df):
        print("No duplicates found")
        return (playlists, data_for_playlists)
    
    df = df.sort_values(by="addedAt")
    df = df[df.duplicated(subset=["title"], keep="last")]
    df = df.sort_values(by="title")
    dupes = df.to_dict(orient="records")
    # FIND DUPES

    # PRINT TABLE WITH DUPLICATES
    print(f"{len(dupes)} Duplicates found:")
    with pd.option_context("display.max_rows", None):
        print(df, end="\n\n")
    # PRINT TABLE WITH DUPLICATES

    # REMOVE DUPLICATE ELEMENTS
    print("Removing duplicates")
    removed_positions: set[int] = set()
    for i, dupe in enumerate(dupes):
        this_pl: Playlist = playlists[dupe["pos"]]

        if this_pl.title != dupe["title"] or this_pl.ratingKey != dupe["id"]:
            continue
        else:
            removed_positions.add(dupe["pos"])
            print(f"Removing: {this_pl.title}")
            this_pl.delete()
            print(f"Progress: {i+1} / {len(dupes)}")
    #REMOVE DUPLICATE ELEMENTS

    #UPDATE PLAYLISTS LIST
    temp = []
    for i in range(len(playlists)):
        if i not in removed_positions:
            temp.append(playlists[i])

    playlists = temp
    data_for_playlists = [Playlist_Data(playlist, pos=i) for i, playlist in enumerate(playlists)]
    #UPDATE PLAYLISTS LIST

    print("Duplicates Removed!")
    return (playlists, data_for_playlists)

def get_target_playlist(server: PlexServer, data_for_playlists: list[Playlist_Data]):
    for i in range(len(data_for_playlists)):
        data_for_playlists[i].title = data_for_playlists[i].title.lower()
    
    while True:
        target_playlist_name = input("Insert Target Playlist Name: ").strip().lower()

        # This either manages to turn the input into a list or it just defaults the parsed value to an empty string so that it fails the verification on isinstance
        try:
            parsed = ast.literal_eval(target_playlist_name)
        except ValueError, SyntaxError:
            parsed = ""

        if isinstance(parsed, list):
            target_playlists: list[Playlist] = []
            target_playlist_name = cast(list[str], parsed)
            lower_case_names = [pl.lower() for pl in target_playlist_name]

            all_matches: list[Playlist_Data] = []

            for name in lower_case_names:
                matches = [pl for pl in data_for_playlists if pl.title==name]

                if not matches:
                    print("One ore more elements of the list have no match", end="\n\n")
                    print(f"Not matched: {name}")
                    all_matches = []
                    break
                else:
                    if len(matches) > 1:
                        matches.sort(key=lambda x: x.addedAt, reverse=True)
                    all_matches.append(matches[0])

            if all_matches:
                all_matches.reverse()
                for match in all_matches:
                    target_playlists.append(server.fetchItem(match.id))
                return target_playlists

        else:
            matches = [pl for pl in data_for_playlists if pl.title==target_playlist_name]
            if not len(matches):
                print("No Match Found", end="\n\n")
            else:
                if len(matches) > 1:
                    matches.sort(key=lambda x: x.addedAt, reverse=True)
                target_playlist: Playlist = server.fetchItem(matches[0].id)
                return target_playlist
    

def plex_sort_compare(video_a: Video, video_b: Video):
    #PLEX USES A CUSTOM SORT ORDER SO THIS IS NECESSARY
    i = 0

    a: str = video_a.title
    b: str = video_b.title

    while i < len(a) and i < len(b):
        char_a = a[i]
        char_b = b[i]

        if char_a == char_b:
            i+= 1
            continue
        
        if char_a == "-" and char_b in [",", "&"]:
            return -1
        if char_b == "-" and char_a in [",", "&"]:
            return 1
        return ord(char_a) - ord(char_b)

    return len(a) - len(b)

def chronologically_sort_target_audio_playlist(target_playlist: Playlist, newest_to_oldest: bool = True):
    pl_items = cast(list[Track], target_playlist.items())
    if not len(pl_items):
            print("Playlist is empty")
    
    elif len(pl_items) == 1:
        print("Playlist only has a single element")
    
    else:
        pl_items.sort(key= lambda t: (-t.addedAt.timestamp() if newest_to_oldest else t.addedAt.timestamp(), t.title)) # I don't use custom sort order for audio tracks.

        target_playlist.moveItem(pl_items[0])
        for i in range(1, len(pl_items)):
            target_playlist.moveItem(pl_items[i], after=pl_items[i-1])

        print("Playlist Sorted!")

def sort_target_video_playlist(target_playlist: Playlist):
    pl_items: list[Video] = target_playlist.items()
    if not len(pl_items):
        print("Playlist is empty")

    elif len(pl_items) == 1:
        print("Playlist only has a single element")

    else:
        pl_items.sort(key=cmp_to_key(plex_sort_compare))

        target_playlist.moveItem(pl_items[0])
        for i in range(1, len(pl_items)):
            target_playlist.moveItem(pl_items[i], after=pl_items[i-1])

        print("Playlist Sorted!")

def save_playlist_items_to_json(target_playlist: Playlist, item_type: Literal["video", "music"], save_path: pathlib.Path=pathlib.Path.home()):
    try:
        if item_type not in ["video", "music"]:
            raise Exception("Invalid value for item type")
        
        pl_items = cast(list[Track | Video], target_playlist.items())
        if not len(pl_items):
            print("Playlist is empty")
            return 

        data_for_items: list[Track_Data | Movie_Data] = []
        for pos, item in enumerate(pl_items):
            match item_type:
                case "music":
                    data = Track_Data(item, pos)
                case "video":
                    data = Movie_Data(item)
            data_for_items.append(data)
            
            with open(save_path, "w", encoding="utf-8") as file:
                json.dump([item.to_dict(False) for item in data_for_items], file, indent=4)
        
        print(f"Wrote playlist items to {save_path}")
    except Exception as err:
        print(err)

def get_list_of_playlists(data_for_playlists: list[Playlist]):
    sort_mode = get_sort_mode()
    data_for_playlists.sort(key=lambda pl: getattr(pl, sort_mode["key"]) , reverse=sort_mode["descending"])

    
    
    pl_names = [f"{pl.title}\n" for pl in data_for_playlists]
    save_path = get_json_save_path(default_name="Playlists", extension=".txt", filetype_description="txt file")
    with open(save_path, "w", encoding="utf-8") as file:
        file.writelines(pl_names)