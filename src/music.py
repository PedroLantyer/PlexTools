from plexapi.audio import Artist, Album, Track

class Artist_Data:
     name: str
     id: int
     pos: int # Index in the original artist list

     def __init__(self, artist: Artist, pos: int):
          self.name = artist.title
          self.id = artist.ratingKey
          self.pos = pos
          
class Track_Data:
     title: str
     id: int
     pos: int # Index in the original artist list

     def __init__(self, track: Track, pos: int):
          self.title = track.title
          self.id = track.ratingKey
          self.pos = pos

def sort_audio_tracks_for_all_artists(artists: list[Artist], data_for_artists: list[Artist_Data]):
    for artist in data_for_artists:
            this_artist: Artist = artists[artist.pos]
            print(f"Sorting for artist: {artist.name}")
            albums: list[Album] = this_artist.albums()
    
            for album in albums:
                print(f"Sorting album: {album.title}")
                tracks: list[Track] = album.tracks()
                track_list = [Track_Data(track, pos=i) for i, track in enumerate(tracks)]
                track_list.sort(key=lambda t: t.title)
    
                for i, track in enumerate(track_list):
                    tracks[track.pos].editTrackNumber(trackNumber=i+1)

    print("Finished sorting audio tracks")
