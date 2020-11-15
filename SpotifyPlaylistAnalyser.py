from collections import Counter
from itertools import islice
from os import getenv
from threading import Thread
from typing import Iterable, List, Tuple, Dict, Any

from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials

spotify = Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        client_id=getenv("SPOTIFY_CLIENT_ID"),
        client_secret=getenv("SPOTIFY_CLIENT_SECRET")
    )
)


class LoadThread(Thread):
    def __init__(self, username: str, max_playlists: int):
        super().__init__()
        self.username = username
        self.max_playlists = max_playlists
        self.playlists: List[Dict[str, Any]] = None

    def run(self):
        self.playlists = list(islice(
            self._get_playlists(self.username), 
            self.max_playlists
        ))

    def join(self):
        super().join()
        return self.playlists

    def _get_playlists(
        self,
        username: str, 
        check_owner = True
    ) -> Iterable[Tuple[str]]:
        try:
            playlists = spotify.user_playlists(username)
        except SpotifyException:
            playlists = None

        while playlists is not None:
            for playlist in playlists["items"]:
                if check_owner and playlist["owner"]["id"] != username:
                    continue
                
                yield playlist
            
            playlists = spotify.next(playlists)


class AnalyseThread(Thread):
    def __init__(self, playlist_ids_names: List[List[str, str]]):
        super().__init__()
        self.playlist_ids_names = playlist_ids_names
        self.top_artists: List[Dict[str, Any]] = None
        self.duplicate_tracks: List[Dict[str, Any]] = None

    def run(self):
        self.top_artists = []
        self.duplicate_tracks = []

        for id_, name in self.playlist_ids_names:            
            artists, count = self._get_top_artists(id_)

            duplicates = self._get_duplicates(id_)

            if artists:
                self.top_artists.append({
                    "playlist": name, 
                    "artists": artists, 
                    "count": count
                })
            
            if duplicates:
                # descending order of track count
                duplicates.sort(key=lambda x: x["count"], reverse=True)

                self.duplicate_tracks.append({
                    "playlist": name, 
                    "duplicates": duplicates
                })

        # descending order of track count
        self.top_artists.sort(key=lambda x: x["count"], reverse=True)
        self.duplicate_tracks.sort(
            key=lambda x: x["duplicates"][0]["count"], 
            reverse=True
        )

    def join(self):
        super().join()
        return self.top_artists, self.duplicate_tracks

    def _get_top_artists(self, playlist_id: str) -> (List[str], int):
        tracks = spotify.playlist_tracks(playlist_id)
        artist_count = Counter()

        while tracks is not None:
            artist_count.update(
                artist["name"].strip() 
                for track in tracks["items"]
                if track["track"] is not None
                for artist in track["track"]["artists"]
            )

            tracks = spotify.next(tracks)

        if not artist_count:
            return [], 0

        top_count = max(artist_count.values())

        top_artists = list(filter(
            lambda x: artist_count[x] == top_count,
            artist_count
        ))
        top_artists.sort(key=str.lower)

        max_artists = 10

        # + 1 because we want at least 2 more to print the short version
        if len(top_artists) > max_artists + 1:
            excess = f"{len(top_artists) - max_artists} others"
            top_artists = [*top_artists[:max_artists], excess]
        
        return top_artists, top_count

    def _get_duplicates(
        self,
        playlist_id: str,
        include_album = False
    ) -> List[Dict[str, Any]]:
        tracks = spotify.playlist_tracks(playlist_id)
        all_meta = {}

        while tracks is not None:
            for track_item in tracks["items"]:
                if track_item["track"] is None:
                    continue

                track = track_item["track"]
                name = track["name"].strip()
                artists = [a["name"].strip() for a in track["artists"]]
                artists.sort(key=str.lower)
                album = track["album"]["name"].strip()

                meta_key = "".join([
                    name,
                    *artists,
                    album if include_album else ""
                ])
                item = all_meta.get(meta_key)

                if item:
                    item["count"] += 1

                    if album.lower() not in map(str.lower, item["albums"]):
                        item["albums"].append(album)
                else:
                    all_meta[meta_key] = {
                        "track": name, 
                        "artists": artists,
                        "albums": [album],
                        "count": 1
                    }

            tracks = spotify.next(tracks)

        return [x for x in all_meta.values() if x["count"] > 1]


if __name__ == "__main__":
    while True:
        print("Ctrl+C then Enter to exit")

        try:
            username = input("Username [spotify]: ").strip() or "spotify"
            max_playlists = int(input("Max playlists [10]: ").strip() or 10)
            
            t = LoadThread(username, max_playlists)
            t.start()
            ids_names = t.join()

            t = AnalyseThread(ids_names)
            t.start()
            top_artists, duplicate_tracks = t.join()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(e)
        else:
            print("\nTop artists:")
            print(*top_artists, sep="\n")
            print("\nDuplicate tracks:") 
            print(*duplicate_tracks, sep="\n")   


# def print_results(
#     playlist_name: str, 
#     num_tracks: int, 
#     top_artists: List[str] = None, 
#     top_count: int = None, 
#     duplicates: List[dict] = None
# ):
#     print(f"\t{playlist_name} - {num_tracks} tracks")

#     if top_artists:
#         print(f"\t\tTop artist(s): ", end="")
#         print(*top_artists, sep=", ", end="")
        
#         if top_count:
#             print(f" with {top_count} track(s) (each)")
#         else:
#             print("")
    
#     if duplicates:
#         print(f"\t\t{len(duplicates)} track(s) with duplicates")

#         for duplicate in duplicates:
#             print(
#                 "\t\t\t\"{name}\" by {artists} on {albums}".format(**duplicate),
#                 end=""
#             )
            
#             if len(duplicate["albums"]) == 1:
#                 print(f" appears {duplicate['count']} times", end="")
            
#             print("")
