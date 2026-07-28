import pandas as pd
from functools import cmp_to_key
from plexapi.playlist import Playlist
from plexapi.video import Video
from plexapi.server import PlexServer

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

def remove_duplicate_playlists(playlists: list[Playlist], data_for_playlists: list[Playlist_Data]):
    #FIND DUPES
    df = pd.DataFrame([vars(playlist) for playlist in data_for_playlists])
    df = df[df.duplicated(subset=["title"], keep=False)]

    if not len(df):
        print("No duplicates found")
        return (playlists, data_for_playlists)
    
    df = df.sort_values(by="addedAt")
    df = df[df.duplicated(subset=["title"], keep="last")]
    df = df.sort_values(by="title")
    dupes = df.to_dict(orient="records")
    #FIND DUPES

    #PRINT TABLE WITH DUPLICATES
    print(f"{len(dupes)} Duplicates found:")
    with pd.option_context("display.max_rows", None):
        print(df, end="\n\n")
    #PRINT TABLE WITH DUPLICATES

    #REMOVE DUPLICATE ELEMENTS
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

def get_target_playlist(server: PlexServer, data_for_playlists: list[Playlist_Data]) -> Playlist:
    while(True):
        target_playlist_name = input("Insert Target Playlist Name: ").strip()
        matches = [pl for pl in data_for_playlists if pl.title.lower()==target_playlist_name.lower()]
        if not len(matches):
            print("No Match Found", end="\n\n")
        else:
            if len(matches) > 1:
                matches.sort(key=lambda x: x.addedAt, reverse=True)
            break

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

def sort_target_video_playlist(target_playlist: Playlist):
    pl_items: list[Video] = target_playlist.items()
    if not len(pl_items):
        print("Playlist is empty")
        exit(0)
    if len(pl_items) == 1:
        print("Playlist only has a single element")
        exit(0)

    pl_items.sort(key=cmp_to_key(plex_sort_compare))

    target_playlist.moveItem(pl_items[0])
    for i in range(1, len(pl_items)):
        target_playlist.moveItem(pl_items[i], after=pl_items[i-1])

    print("Playlist Sorted!")
