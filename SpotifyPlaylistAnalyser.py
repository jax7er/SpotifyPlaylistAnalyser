import string
from collections import Counter
from os import getenv

import spotipy.util as util
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


def get_top_artists(tracks: dict) -> (list, int):
    count = Counter()

    while tracks is not None:
        count.update(
            artist["name"].strip() 
            for track in tracks["items"]
            for artist in track["track"]["artists"]
        )

        tracks = spotify.next(tracks)

    top_count = max(count.values())

    top_artists = [
        name
        for name, count in count.items()
        if count == top_count
    ]

    return top_artists, top_count


def get_duplicates(tracks: dict) -> list:
    duplicate_meta = {}
    all_meta_processed = []

    while tracks is not None:
        for track in tracks["items"]:
            name = track["track"]["name"]
            artists = ", ".join(artist["name"].strip() for artist in track["track"]["artists"])
            album = track["track"]["album"]["name"]

            meta_processed = "".join(
                c.lower()
                for c in (name + artists + album)
                if c.isalnum()
            )

            if meta_processed in all_meta_processed:
                if meta_processed in duplicate_meta:
                    duplicate_meta[meta_processed]["count"] += 1
                else:
                    duplicate_meta[meta_processed] = {"name": name, "artists": artists, "album": album, "count": 2}

            all_meta_processed.append(meta_processed)

        tracks = spotify.next(tracks)

    return list(duplicate_meta.values())


def print_results(playlist_name, top_artists, top_count, duplicates):
    print(f"\t{playlist_name}")

    print(f"\t\tTop artist(s): \"", end="")
    print(*top_artists, sep=", ", end="")
    print(f"\", track count: {top_count}")
    
    if not duplicates:
        print(f"\t\tNo duplicate tracks")
    else:
        print(f"\t\t{len(duplicates)} track(s) with duplicates")

        for duplicate in duplicates:
            print("\t\t\t\"{name}\" by "
                    "\"{artists}\" on "
                    "\"{album}\" repeats "
                    "{count} times".format(**duplicate))


def analyse(username: str):
    try:
        playlists = spotify.user_playlists(username)
    except SpotifyException:
        playlists = None
    
    while playlists is not None:
        for playlist in playlists["items"]:
            if playlist["owner"]["id"] != username:
                continue
            
            tracks = spotify.playlist_tracks(playlist["id"])

            top_artists, top_count = get_top_artists(tracks)

            duplicates = get_duplicates(tracks)

            print_results(playlist["name"], top_artists, top_count, duplicates)

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
