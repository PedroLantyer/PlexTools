from typing import Literal, cast, TypedDict

VIDEO_SORT_KEYS = Literal["title", "addedAt"]
MUSIC_SORT_KEYS = Literal["title", "artist", "album", "addedAt"]

class SortMode(TypedDict):
    key: VIDEO_SORT_KEYS | MUSIC_SORT_KEYS
    descending: bool

def get_sort_mode(type: Literal["video", "music"] = "video"):
    VIDEO_OPTIONS = ["TITLE ASC", "TITLE DESC", "ADDED_AT ASC", "ADDED_AT DESC"]
    MUSIC_OPTIONS = ["TITLE ASC", "TITLE DESC", "ARTIST ASC", "ARTIST DESC", "ALBUM ASC", "ALBUM DESC", "ADDED_AT ASC", "ADDED_AT DESC"]

    match type:
        case "video":
            options = VIDEO_OPTIONS
        case "music":
            options = MUSIC_OPTIONS

    selected_sort = ""
    while selected_sort == "":
        print("SELECT SORT MODE")
        for i, option in enumerate(options, start=1):
            print(f"{i} - {option}")

        try:
            option_chosen = input().strip().upper()

            if not len(option_chosen):
                print("Couldn't Understand. Try again", end="\n\n")
            else: 
                fp = float(option_chosen)
                choice = int(fp)
                if choice >= 1 and choice <= len(options):
                    print("GOT HERE")
                    selected_sort = options[choice-1]
                    break
                print("Couldn't Understand. Try again", end="\n\n")

        except:
            print("Couldn't Understand. Try again", end="\n\n")  

    key_and_order = selected_sort.split()
    if key_and_order[0] == "ADDED_AT":
        key = "addedAt"
    else:
        key = key_and_order[0].lower()

    return SortMode(key=key, descending=key_and_order[1]=="DESC")