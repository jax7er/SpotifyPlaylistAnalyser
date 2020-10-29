from collections import Counter
from itertools import islice
from os import getenv
from threading import Thread
from typing import Iterable, List, Tuple

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
    def __init__(self, username, max_playlists):
        super().__init__()
        self.username = username
        self.max_playlists = max_playlists

    def run(self):
        self.ids_names = list(islice(
            self._get_playlist_ids_names(self.username), 
            self.max_playlists
        ))

    def join(self):
        super().join()
        return self.ids_names

    def _get_playlist_ids_names(
        self,
        username: str, 
        check_owner: bool = False
    ) -> Iterable[Tuple[str]]:
        try:
            playlists = spotify.user_playlists(username)
        except SpotifyException:
            playlists = None

        while playlists is not None:
            for playlist in playlists["items"]:
                if check_owner and playlist["owner"]["id"] != username:
                    continue
                
                yield playlist["id"], playlist["name"]
            
            playlists = spotify.next(playlists)


class AnalyseThread(Thread):
    def __init__(self, id_names):
        super().__init__()
        self.id_names = id_names

    def run(self):
        self.top_artists = []
        self.duplicate_tracks = []

        for p_id, p_name in self.id_names:
            tracks = spotify.playlist_tracks(p_id)

            artists, count = self._get_top_artists(tracks)

            duplicates = self._get_duplicates(tracks)

            if artists:
                self.top_artists.append({
                    "playlist": p_name, 
                    "artists": artists, 
                    "count": count
                })
            
            if duplicates:
                # descending order of track count
                duplicates.sort(key=lambda x: x["count"], reverse=True)

                self.duplicate_tracks.append((p_name, duplicates))

        # descending order of track count
        self.top_artists.sort(
            key=lambda x: x["count"], 
            reverse=True
        )
        self.duplicate_tracks.sort(
            key=lambda x: x[1][0]["count"], 
            reverse=True
        )

    def join(self):
        super().join()
        return self.top_artists, self.duplicate_tracks

    def _get_top_artists(self, tracks: dict) -> (List[str], int):
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

        top_artists = list(sorted(
            name
            for name, count in artist_count.items()
            if count == top_count
        ))

        max_artists = 10

        # + 1 because we want at least 2 more to print the short version
        if len(top_artists) > max_artists + 1:
            return (
                [
                    *top_artists[:max_artists], 
                    f"and {len(top_artists) - max_artists} others"
                ],
                top_count
            )
        else:
            return top_artists, top_count

    def _get_duplicates(
        self,
        tracks: dict,
        include_album: bool = True
    ) -> List[dict]:
        all_meta = {}

        while tracks is not None:
            for track in tracks["items"]:
                if track["track"] is None:
                    continue

                name = track["track"]["name"]
                album = track["track"]["album"]["name"]
                artists_gen = (
                    artist["name"].strip()
                    for artist in track["track"]["artists"]
                )
                artists = list(sorted(artists_gen, key=str.lower))

                meta_key = "".join(
                    c.lower()
                    for c
                    in name + "".join(artists) + (album if include_album else "")
                    if c.isalnum()
                )

                if meta_key in all_meta:
                    item = all_meta[meta_key]

                    item["count"] += 1

                    if album.lower() not in map(str.lower, item["albums"]):
                        item["albums"].append(album)
                else:
                    all_meta[meta_key] = {
                        "name": name, 
                        "artists": artists,
                        "albums": [album],
                        "count": 1
                    }

            tracks = spotify.next(tracks)

        return [
            x
            for x in all_meta.values()
            if x["count"] > 1
        ]


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
            print("Top artists:")
            print(*top_artists, sep="\n")
            print("")
            print("Duplicate tracks:") 
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
