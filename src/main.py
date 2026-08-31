import os
from dotenv import load_dotenv
from typing import cast, Literal
from datetime import datetime
from time import sleep
from plexapi.server import PlexServer
from plexapi.library import Library, LibrarySection
from plexapi.playlist import Playlist
from plexapi.audio import Artist
from plexapi.video import Movie
from plexapi.exceptions import Unauthorized, NotFound, BadRequest
from music import Artist_Data, sort_audio_tracks_for_all_artists
from movie import Movie_Data
from playlist import *
from json_utils import *

def get_target_section_id() -> int:
    print("Sections available:")
    for section in sections:
        print(section["title"])
    print("\n")
    
    while(True):
            selected_section_title = input("Insert Target Section Title: ").strip().lower()
            match = [section for section in sections if section["title"].lower()==selected_section_title]
            if not match:
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

def get_artist_task() -> Literal["Sort tracks for all artists", "Save playlist item data to JSON", "Add playlist from JSON", "Sort Playlist By Added At"]:
    while True:
        task_options = ["Sort tracks for all artists", "Save playlist item data to JSON", "Add playlist from JSON", "Sort Playlist By Added At"]

        print("SELECT CHOSEN TASK")
        for i, task in enumerate(task_options, 1):
            print(f"{i} - {task}")
        print("0 - EXIT")

        option_chosen = input("Chosen Option: ").strip()
        if not len(option_chosen):
            print("Couldn't Understand. Try again", end="\n\n")
        else:
            try:
                fp = float(option_chosen)
                option = int(fp)
                if option == 0:
                    return "EXIT"
                if option >= 1 and option <= len(task_options):
                    return task_options[option - 1]
                print("Couldn't Understand. Try again", end="\n\n")
            except:
                print("Couldn't Understand. Try again", end="\n\n")          

def get_video_task() -> Literal["Remove Duplicate Playlists", "Sort Playlist", "Save playlist item data to JSON", "Add playlist from JSON", "Add Smart Playlists From JSON", "Duplicate Playlist", "Get list of Playlists", "Refetch Playlists"]:
    while True:
        task_options = ["Remove Duplicate Playlists", "Sort Playlist", "Save playlist item data to JSON", "Add playlist from JSON", "Add Smart Playlists From JSON", "Duplicate Playlist", "Get list of Playlists", "Refetch Playlists"]

        print("SELECT CHOSEN TASK")
        for i, task in enumerate(task_options, 1):
            print(f"{i} - {task}")
        print("0 - EXIT")

        option_chosen = input("Chosen Option: ").strip()
        if not len(option_chosen):
            print("Couldn't Understand. Try again", end="\n\n")
        else:
            try:
                fp = float(option_chosen)
                option = int(fp)
                if option == 0:
                    return "EXIT"
                if option >= 1 and option <= len(task_options):
                    return task_options[option - 1]
                print("Couldn't Understand. Try again", end="\n\n")
            except:
                print("Couldn't Understand. Try again", end="\n\n")          

def get_all_videos_in_last_two_hours():
    videos = cast(list[Movie], selected_section.all())
    min_date = datetime.fromtimestamp(int(datetime.now().timestamp()) - 7200)
    videos_in_time_range = [video for video in videos if video.addedAt >= min_date]
    videos_in_time_range.sort(key=lambda v: v.title)
    
    file_data: list[dict] = [{"title": video.title, "path": video.locations[0]} for video in videos_in_time_range if len(video.locations)]
    print(f"Found {len(videos_in_time_range)} Videos")
    
    save_path = get_json_save_path(default_name="Videos")
    with open(save_path, "w", encoding="utf-8") as json_file:
        json.dump(file_data, json_file, indent=4)
    print(f"Wrote File List To JSON at \"{save_path}\"")

if __name__ == "__main__":
    load_dotenv()
    PLEX_URL = os.getenv("PLEX_URL")
    PLEX_TOKEN = os.getenv("PLEX_TOKEN")

    server = connect_to_server()
    lib: Library = server.library

    sections = [{"id": sect.key, "title": sect.title, "type": sect.type} for sect in lib.sections()]
    sections.sort(key=lambda x: x["title"])

    target_section_id = get_target_section_id()
    selected_section = cast(LibrarySection, lib.sectionByID(target_section_id))
    section_type = cast(Literal["movie", "photo", "show", "artist"], selected_section.type)

    match section_type:
        case "movie":
            playlists: list[Playlist] = selected_section.playlists()
            data_for_playlists = [Playlist_Data(playlist, pos=i) for i, playlist in enumerate(playlists)]

            while True:
                task = get_video_task()
                match task:
                    case "Remove Duplicate Playlists":
                        playlists: list[Playlist] = selected_section.playlists()
                        data_for_playlists = [Playlist_Data(playlist, pos=i) for i, playlist in enumerate(playlists)]
                        playlists, data_for_playlists = remove_duplicate_playlists(playlists, data_for_playlists)
                        playlists: list[Playlist] = selected_section.playlists()
                        data_for_playlists = [Playlist_Data(playlist, pos=i) for i, playlist in enumerate(playlists)]

                    case "Sort Playlist":
                        target_playlist = get_target_playlist(server, data_for_playlists)

                        if isinstance(target_playlist, Playlist):
                            target_playlist = [target_playlist]
                        
                        for playlist in target_playlist:
                            if playlist.smart:
                                print(f"Can't sort Smart Playlist \"{playlist.title}\"")
                            else:
                                sort_target_video_playlist(playlist)

                    case "Save playlist item data to JSON":
                        target_playlist = get_target_playlist(server=server, data_for_playlists=data_for_playlists)

                        if isinstance(target_playlist, Playlist):
                            target_playlist = [target_playlist]

                        for playlist in target_playlist:
                            videos_in_playlist: Video = playlist.items()
                            save_path = get_json_save_path(playlist.title)
                            save_playlist_items_to_json(playlist, "video", save_path)

                    case "Add playlist from JSON":
                        file_path = get_json_file_path()

                        if file_path:
                            items = get_playlist_items_from_json(file_path)
                            if items:
                                playlist_name = file_path.stem
                                videos = get_items_based_on_json(server, items)
                                server.createPlaylist(title=playlist_name, items=videos)
                                playlists: list[Playlist] = selected_section.playlists()
                                data_for_playlists = [Playlist_Data(playlist, pos=i) for i, playlist in enumerate(playlists)]
                                print(f"Playlist \"{playlist_name}\" Created")

                    case "Add Smart Playlists From JSON":
                        file_path = get_json_file_path()

                        if file_path:
                            with open(file_path, "r", encoding="utf-8") as file:
                                playlists_from_json: list[dict] = json.load(file)

                            playlists_from_json.reverse()
                            for i, pl in enumerate(playlists_from_json):
                                if i:
                                    sleep(1)
                                server.createPlaylist(title=pl["title"], smart=True, section=selected_section, sort=pl["sort"], filters=pl["filters"])
                                print(f"Smart Playlist \"{pl["title"]}\" Created")

                        playlists: list[Playlist] = selected_section.playlists()
                        data_for_playlists = [Playlist_Data(playlist, pos=i) for i, playlist in enumerate(playlists)]

                    case "Duplicate Playlist":
                        target_playlist = get_target_playlist(server=server, data_for_playlists=data_for_playlists)
                        
                        if isinstance(target_playlist, Playlist):
                            target_playlist = [target_playlist]

                        for i, playlist in enumerate(target_playlist):
                            if playlist.smart:
                                filters: dict = playlist.filters()
                                if i:
                                    sleep(1)
                                server.createPlaylist(title=playlist.title, section=selected_section, smart=True, sort=filters.get("sort"), filters=filters.get("filters"))
                                print(f"Playlist \"{playlist.title}\" Duplicated")
                            else:
                                videos_in_playlist: Video = playlist.items()
                                if videos_in_playlist is not None:
                                    if i:
                                        sleep(1) # Plex only stores seconds in it's DB so a 1 second delay between each addition is necessary to maintain the correct order
                                    server.createPlaylist(title=playlist.title, items=videos_in_playlist)
                                    print(f"Playlist \"{playlist.title}\" Duplicated")

                        playlists: list[Playlist] = selected_section.playlists()
                        data_for_playlists = [Playlist_Data(playlist, pos=i) for i, playlist in enumerate(playlists)]

                    case "Get list of Playlists":
                        playlists = cast(list[Playlist], selected_section.playlists())
                        if not playlists:
                            print("No Playlists Found")
                        data_for_playlists = [Playlist_Data(playlist, pos=i) for i, playlist in enumerate(playlists)]

                        get_list_of_playlists(data_for_playlists)

                    case "Refetch Playlists":
                        playlists: list[Playlist] = selected_section.playlists()
                        data_for_playlists = [Playlist_Data(playlist, pos=i) for i, playlist in enumerate(playlists)]


                    case _:
                        break

        case "artist":
            while True:
                task = get_artist_task()
                match task:
                    case "Sort tracks for all artists":
                        artists: list[Artist] = selected_section.all()
                        data_for_artists = [Artist_Data(artist, pos=i) for i, artist in enumerate(artists)]
                        sort_audio_tracks_for_all_artists(artists, data_for_artists)


                    case "Save playlist item data to JSON":
                        playlists: list[Playlist] = selected_section.playlists()
                                    
                        data_for_playlists = [Playlist_Data(playlist, pos=i) for i, playlist in enumerate(playlists)]
                        data_for_playlists.sort(key= lambda pl: pl.title)
                                    
                        for playlist in data_for_playlists:
                            playlist.print_playlist_data()
                        print("\n")
                                    
                        target_playlist = get_target_playlist(server, data_for_playlists)

                        if isinstance(target_playlist, Playlist):
                            target_playlist = [target_playlist]

                        for playlist in target_playlist:
                            save_path = get_json_save_path(playlist.title)
                            save_playlist_items_to_json(playlist, "music", save_path)

                    case "Add playlist from JSON":
                        file_path = get_json_file_path()

                        if file_path:
                            items = get_playlist_items_from_json(file_path)
                            if items is not None:
                                playlist_name = file_path.stem
                                tracks = get_items_based_on_json(server, items)
                                server.createPlaylist(title=playlist_name, items=tracks)
                                print(f"Playlist \"{playlist_name}\" Created")

                    case "Sort Playlist By Added At":
                        playlists: list[Playlist] = selected_section.playlists()

                        data_for_playlists = [Playlist_Data(playlist, pos=i) for i, playlist in enumerate(playlists)]
                        data_for_playlists.sort(key= lambda pl: pl.title)

                        for playlist in data_for_playlists:
                            playlist.print_playlist_data()
                        print("\n")
                        
                        target_playlist = get_target_playlist(server, data_for_playlists)

                        if isinstance(target_playlist, Playlist):
                            target_playlist = [target_playlist]
                        
                        for playlist in target_playlist:
                            chronologically_sort_target_audio_playlist(playlist)

                    case _:
                        break

        case _:
            print("No utilities for photo and show libraries")

    print("Goodbye")