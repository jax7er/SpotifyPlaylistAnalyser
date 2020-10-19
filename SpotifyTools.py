import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
import string


def process_meta(s):
    return s.translate(str.maketrans('', '', ' ' + string.punctuation)).lower()


def find_print_top_artist(p):
    tracks = p['tracks']

    all_artists = {}
    while True:
        for track in tracks['items']:
            artists = [artist['name'].strip() for artist in track['track']['artists']]

            for artist in artists:
                key = artist.lower()

                if key in all_artists:
                    all_artists[key]['count'] += 1
                else:
                    all_artists[key] = {'name': artist, 'count': 1}

        if tracks['next']:
            tracks = sp.next(tracks)
        else:
            break

    top_artist = {'name': '', 'count': 0}
    multiple = False
    for _, v in all_artists.items():
        if v['count'] == top_artist['count']:
            multiple = True
            top_artist['name'] += f', {v["name"]}'
        elif v['count'] > top_artist['count']:
            multiple = False
            top_artist = v

    if multiple:
        print(f'\tTop artists are "{top_artist["name"]}" with {top_artist["count"]} track(s) each')
    else:
        print(f'\tTop artist is "{top_artist["name"]}" with {top_artist["count"]} track(s)')


def find_print_playlist_duplicates(p):
    tracks = p['tracks']

    duplicate_meta = {}
    all_meta_processed = []
    while True:
        for track in tracks['items']:
            name = track['track']['name']
            artists = ', '.join(artist['name'] for artist in track['track']['artists'])
            album = track['track']['album']['name']
            meta_processed = process_meta(name + artists + album)

            if meta_processed in all_meta_processed:
                if meta_processed in duplicate_meta:
                    duplicate_meta[meta_processed]['count'] += 1
                else:
                    duplicate_meta[meta_processed] = {'name': name, 'artists': artists, 'album': album, 'count': 2}

            all_meta_processed.append(meta_processed)

        if tracks['next']:
            tracks = sp.next(tracks)
        else:
            break

    if not duplicate_meta:
        print(f'\tNo duplicates!')
    else:
        print(f'\t{len(duplicate_meta)} track(s) with duplicates...')

        for _, meta in duplicate_meta.items():
            print(f'\t"{meta["name"]}" by "{meta["artists"]}" on "{meta["album"]}"')
            print(f'\t\t{meta["count"]} occurrences')


client_credentials_manager = SpotifyClientCredentials()

scope = 'playlist-read'
# token = util.prompt_for_user_token('06mehmej', scope)

username = '06mehmej'

sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
# sp = spotipy.Spotify(auth=token)

playlists = sp.user_playlists(username)

analyse_playlists_containing = None

for playlist in playlists['items']:
    if analyse_playlists_containing:
        if not any(name in playlist['name'] for name in analyse_playlists_containing):
            continue

    use_playlist = sp.user_playlist(username, playlist['id'])

    print(use_playlist['name'])

    find_print_top_artist(use_playlist)
    find_print_playlist_duplicates(use_playlist)
