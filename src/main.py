import os
from dotenv import load_dotenv
from functools import cmp_to_key
import pandas as pd
from typing import cast, Literal
from plexapi.server import PlexServer
from plexapi.library import Library, LibrarySection
from plexapi.playlist import Playlist
from plexapi.video import Video
from plexapi.audio import Artist, Album, Track
from plexapi.exceptions import Unauthorized, NotFound, BadRequest

def get_target_section_id() -> int:
    print("Sections available:")
    for section in sections:
        print(section["title"])
    print("\n")
    
    while(True):
            selected_section_title = input("Insert Target Section Title: ").strip()
            match = [section for section in sections if section["title"].lower()==selected_section_title.lower()]
            if not len(match):
                print("Section not found", end="\n\n")
            else:
                return match[0]["id"]

def get_target_playlist() -> Playlist:
    while(True):
        target_playlist_name = input("Insert Target Playlist Name: ").strip()
        matches = [pl for pl in playlist_names if pl["title"].lower()==target_playlist_name.lower()]
        if not len(matches):
            print("No Match Found", end="\n\n")
        else:
            if len(matches) > 1:
                matches.sort(key=lambda x: x["addedAt"], reverse=True)
            break

    target_playlist: Playlist = server.fetchItem(matches[0]["id"])
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

def sort_target_playlist():
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

def connect_to_server():
    try:
        server = PlexServer(PLEX_URL, PLEX_TOKEN)
        return server
    except Exception as error:
        if isinstance(error, Unauthorized):
            print("ERROR 401: Unauthorized")
        elif isinstance(error, NotFound):
            print("ERROR 404: Not Found")
        elif isinstance(error, BadRequest):
            print("ERROR 400: Bad Request")
        else:
            print(error)
        print("Failed to connect to PLEX Server\nExiting")
        exit(1)

def remove_duplicate_playlists():
    global playlists, playlist_names

    #FIND DUPES
    df = pd.DataFrame(playlist_names)
    df = df[df.duplicated(subset=["title"], keep=False)]

    if not len(df):
        print("No duplicates found")
        return
    
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
    playlist_names = [{"title": pl.title,"id": pl.ratingKey, "addedAt": pl.addedAt.isoformat(), "pos": i} for i, pl in enumerate(playlists)]
    #UPDATE PLAYLISTS LIST
    print("Duplicates Removed!")

def sort_audio_tracks_for_all_artists():
    for artist in artist_names:
            this_artist: Artist = artists[artist["pos"]]
            print(f"Sorting for artist: {this_artist.title}")
            albums: list[Album] = this_artist.albums()
    
            for album in albums:
                print(f"Sorting album: {album.title}")
                tracks: list[Track] = album.tracks()
                track_list = [{"title": track.title, "id": track.ratingKey, "pos": i} for i, track in enumerate(tracks)]
                track_list.sort(key=lambda t: t["title"])
    
                for i, track in enumerate(track_list):
                    tracks[cast(int, track["pos"])].editTrackNumber(trackNumber=i)
    print("Finished sorting audio tracks")

if __name__ == "__main__":
    load_dotenv()
    PLEX_URL = os.getenv("PLEX_URL")
    PLEX_TOKEN = os.getenv("PLEX_TOKEN")

    server = connect_to_server()
    lib: Library = server.library

    sections = [{"id": sect.key, "title": sect.title, "type": sect.type} for sect in lib.sections()]
    sections.sort(key=lambda x: x["title"])

    target_section_id = get_target_section_id()
    selected_section: LibrarySection = cast(LibrarySection, lib.sectionByID(target_section_id))
    section_type = cast(Literal["movie", "photo", "show", "artist"], selected_section.type)

    match(section_type):
        case "movie":
            playlists: list[Playlist] = selected_section.playlists()
            playlist_names = [{"title": pl.title,"id": pl.ratingKey, "addedAt": pl.addedAt.isoformat(), "pos": i} for i, pl in enumerate(playlists)]

            remove_duplicate_playlists()
            target_playlist: Playlist = get_target_playlist()
            sort_target_playlist()

        case "artist":
            artists: list[Artist] = selected_section.all()
            artist_names = [{"name": artist.title, "id": artist.ratingKey, "pos": i} for i, artist in enumerate(artists)]
            sort_audio_tracks_for_all_artists() 

        case _:
            print("No utilities for photo and show libraries")