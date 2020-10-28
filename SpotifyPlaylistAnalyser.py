import string
from collections import Counter
from os import getenv
from typing import List, Tuple, Iterable

from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials


spotify = Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        client_id=getenv("SPOTIFY_CLIENT_ID"),
        client_secret=getenv("SPOTIFY_CLIENT_SECRET")
    )
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


def get_duplicates(tracks: dict, include_album: bool = True) -> List[dict]:
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


def print_results(
    playlist_name: str, 
    num_tracks: int, 
    top_artists: List[str] = None, 
    top_count: int = None, 
    duplicates: List[dict] = None
):
    print(f"\t{playlist_name} - {num_tracks} tracks")

    if top_artists:
        print(f"\t\tTop artist(s): ", end="")
        print(*top_artists, sep=", ", end="")
        
        if top_count:
            print(f" with {top_count} track(s) (each)")
        else:
            print("")
    
    if duplicates:
        print(f"\t\t{len(duplicates)} track(s) with duplicates")

        for duplicate in duplicates:
            print(
                "\t\t\t\"{name}\" by {artists} on {albums}".format(**duplicate),
                end=""
            )
            
            if len(duplicate["albums"]) == 1:
                print(f" appears {duplicate['count']} times", end="")
            
            print("")


def get_playlist_ids_names(username: str, check_owner: bool = False) -> Iterable[Tuple[str]]:
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


def analyse(
    username: str = "spotify",
    check_owner: bool = False, 
    analysis: str = "all"
):
    try:
        playlists = spotify.user_playlists(username)
    except SpotifyException:
        playlists = None
    
    if playlists is None:
        print(f"User \"{username}\" is invalid or has no playlists")
    else:
        print(f"{username} - owns/follows {playlists['total']} playlist(s)")
    
    for p_id, p_name in get_playlist_ids_names(username, check_owner):            
        tracks = spotify.playlist_tracks(p_id)

        # ensure the playlist has at least one track
        if tracks is None:
            continue
        
        top_artists = top_count = duplicates = None

        if analysis in "top all".split():
            top_artists, top_count = get_top_artists(tracks)

        if analysis in "dup all".split():
            duplicates = get_duplicates(tracks)

        if any((top_artists, top_count, duplicates)):
            print_results(
                p_name, 
                tracks["total"], 
                top_artists, 
                top_count, 
                duplicates
            )


def main():
    try:
        username = input("Spotify username [SPOTIFY]: ").strip() or "spotify"
        check_owner = input("Check owner [y|N]: ").strip().lower() == "y"
        
        analysis = ""
        while analysis not in "top dup all".split():
            analysis = input("Analysis [top|dup|ALL]: ").strip().lower() or "all"
        
        analyse(username, check_owner, analysis)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        print(e)


if __name__ == "__main__":
    while True:
        try:
            main()
        except KeyboardInterrupt:
            break
