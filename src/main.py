import os
from dotenv import load_dotenv
from typing import cast, Literal
from plexapi.server import PlexServer
from plexapi.library import Library, LibrarySection
from plexapi.playlist import Playlist
from plexapi.audio import Artist
from plexapi.exceptions import Unauthorized, NotFound, BadRequest
from music import Artist_Data, sort_audio_tracks_for_all_artists
from playlist import  Playlist_Data, remove_duplicate_playlists, get_target_playlist, sort_target_video_playlist

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
            data_for_playlists = [Playlist_Data(playlist, pos=i) for i, playlist in enumerate(playlists)]

            playlists, data_for_playlists = remove_duplicate_playlists(playlists, data_for_playlists)

            target_playlist: Playlist = get_target_playlist(server, data_for_playlists)
            sort_target_video_playlist(target_playlist)

        case "artist":
            artists: list[Artist] = selected_section.all()
            data_for_artists = [Artist_Data(artist, pos=i) for i, artist in enumerate(artists)]

            sort_audio_tracks_for_all_artists(artists, data_for_artists) 

        case _:
            print("No utilities for photo and show libraries")