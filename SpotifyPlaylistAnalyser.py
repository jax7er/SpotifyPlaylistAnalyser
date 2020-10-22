import string
from collections import Counter
from os import getenv
from typing import List

from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials

CLIENT_ID = getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET")

credentials_manager = SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
)

spotify = Spotify(
    client_credentials_manager=credentials_manager
)


def get_top_artists(tracks: dict) -> (List[str], int):
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

    top_artists = [
        name
        for name, count in artist_count.items()
        if count == top_count
    ]

    if len(top_artists) == len(artist_count):
        return ["All artists have same track count"], top_count
    else:
        return top_artists, top_count


def get_duplicates(tracks: dict) -> List[dict]:
    duplicate_meta = {}
    all_meta_processed = set()

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
            artists = ", ".join(sorted(artists_gen, key=str.lower))

            meta_filtered = filter(str.isalnum, name + artists + album)
            meta_processed = "".join(meta_filtered).lower()

            if meta_processed in all_meta_processed:
                if meta_processed in duplicate_meta:
                    duplicate_meta[meta_processed]["count"] += 1
                else:
                    duplicate_meta[meta_processed] = {
                        "name": name, 
                        "artists": artists,
                        "album": album, 
                        "count": 2
                    }
            else:
                all_meta_processed.add(meta_processed)

        tracks = spotify.next(tracks)

    return list(duplicate_meta.values())


def print_results(
    playlist_name: str, 
    num_tracks: int, 
    top_artists: List[str], 
    top_count: int, 
    duplicates: List[dict]
):
    print(f"\t{playlist_name} - {num_tracks} tracks")

    print(f"\t\tTop artist(s): ", end="")
    print(*top_artists, sep=", ", end="")
    print(f" with {top_count} track(s) (each)")
    
    if not duplicates:
        print(f"\t\tNo duplicate tracks")
    else:
        print(f"\t\t{len(duplicates)} track(s) with duplicates")

        for duplicate in duplicates:
            print(
                "\t\t\t"
                "\"{name}\" by "
                "\"{artists}\" on "
                "\"{album}\" appears "
                "{count} times".format(**duplicate)
            )


def analyse(username: str):
    try:
        playlists = spotify.user_playlists(username)
    except SpotifyException:
        playlists = None
    
    if playlists is None:
        print(f"User \"{username}\" is invalid or has no playlists")
    else:
        print(f"{username} - owns/follows {playlists['total']} playlist(s)")
    
    while playlists is not None:
        for playlist in playlists["items"]:
            # ensure the playlist was created by the user
            # if playlist["owner"]["id"] != username:
            #     continue
            
            tracks = spotify.playlist_tracks(playlist["id"])

            # ensure the playlist has at least one track
            if tracks is None:
                continue
            
            top_artists, top_count = get_top_artists(tracks)

            duplicates = get_duplicates(tracks)

            print_results(
                playlist["name"], 
                tracks["total"], 
                top_artists, 
                top_count, 
                duplicates
            )

        playlists = spotify.next(playlists)


def main():
    username = input("Spotify username: ").strip()

    analyse(username)


if __name__ == "__main__":
    while True:
        try:
            main()
        except KeyboardInterrupt:
            break
