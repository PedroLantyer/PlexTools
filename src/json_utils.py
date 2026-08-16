import json
import pathlib
from typing import cast
import tkinter as tk
from tkinter import filedialog
from plexapi.audio import Track
from plexapi.video import Video
from plexapi.server import PlexServer
from plexapi.exceptions import NotFound
from music import Track_Data_From_JSON

def get_json_file_path():
    root = tk.Tk()

    # HIDE THE BASE TKINTER WINDOW
    root.withdraw()
    root.attributes("-topmost", True)
    # HIDE THE BASE TKINTER WINDOW

    file_path = filedialog.askopenfilename(title="Select JSON file", filetypes=[("JSON files", "*.json")])
    root.destroy()

    if not len(file_path):
        return None
    return pathlib.Path(file_path)

def get_playlist_items_from_json(file_path: str):
    try:
        with open(file_path, "r") as file:
            content = cast(list[dict], json.load(file))
            #items_for_new_playlist: list[dict] = []   
            items_for_new_playlist: list[Track_Data_From_JSON] = []   

            if bool(content) and isinstance(content, list) and all(isinstance(e, dict) for e in content): # Checks if content of the JSON is a list of dicts that is not empty
                for item in content:
                    lower_case_keys = set(item.keys())
                    if not {"id", "title"}.issubset(lower_case_keys):
                        raise Exception("Invalid keys for JSON. JSON needs to include the attributes \"id\" and \"title\" for each object")
                    #items_for_new_playlist.append({"id": int(item["id"]), "title": item["title"]})
                    items_for_new_playlist.append(Track_Data_From_JSON(title=item["title"], id=int(item["id"])))
                return items_for_new_playlist
            else:
                raise Exception("Empty or Invalid")

    except ValueError:
        print("Invalid id for one or more keys")
        return None

    except Exception as err:
        print(err)
        return None  

def get_items_based_on_json(server: PlexServer, metadata_for_tracks: list[Track_Data_From_JSON]):
    items: list[Track | Video] = []
    for metadata in metadata_for_tracks:
        try: 
            item = cast(Track | Video, server.fetchItem(metadata["id"]))
            items.append(item)
        except NotFound:
            print(f"WARNING: {metadata["title"]} not found in server")
            items.append()
        except Exception as err:
            print(err)

    """
    ids_found = set([item.ratingKey for item in items])
    mismatches = [metadata for metadata in metadata_for_tracks if metadata["id"] in ids_found]

    if len(mismatches):
        print(f"Found {len(mismatches)} mismatches")
        option_chosen = input(f"Type \"ALL\" to add all anyway, \"NONE\" to skip all or anything else to decide for each case: ").strip().lower()

        if option_chosen == "none":
            metadata
            

    print(mismatches) 
    """

    return items

def pick_json_save_path(default_name: str = ""):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    save_path = filedialog.asksaveasfilename(initialfile=default_name, defaultextension=".json", filetypes=[("JSON files", "*.json")])
    root.destroy()

    if not len(save_path):
        save_path = pathlib.Path.home()
        dl_path = save_path.joinpath("Downloads")

        if pathlib.Path.exists(dl_path):
            save_path = dl_path

        save_path = save_path.joinpath("Untitled.json")
        print(f"Since no path was defined, file was saved to:\n{save_path}")

    return save_path