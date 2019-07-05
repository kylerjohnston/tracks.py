#!/usr/bin/env python3
"""
tracks.py is an application to track and compare your Spotify and Google Play Music libraries.
"""

# These are the columns that will be written for the GPM CSV export.
# Columns excluded by default that can be added: 'id', 'totalDiscCount',
# 'discNumber', 'storeId', 'nid', 'estimatedSize', 'albumId',
# 'beatsPerMinute', 'kind', 'clientId'
# See https://unofficial-google-music-api.readthedocs.io/en/latest/reference/mobileclient.html
GPM_EXPORT_COLS = ['comment',
                   'rating',
                   'composer',
                   'year',
                   'creationTimestamp',
                   'album',
                   'title',
                   'recentTimestamp',
                   'albumArtist',
                   'trackNumber',
                   'deleted',
                   'totalTrackCount',
                   'genre',
                   'playCount',
                   'artist',
                   'lastModifiedTimestamp',
                   'durationMillis']

from gmusicapi import Mobileclient
from spotify_token import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
import spotipy
import spotipy.util as util
import csv
import os
import hashlib
import time
import operator

class MusicLibrary:
    def __init__(self):
        self.library = []
        self.tracks = set()
        self.track_keys = ['title',
                           'album',
                           'artist',
                           'track_number',
                           'album_artist',
                           'release_date',
                           'creation_timestamp',
                           'duration_ms',
                           'explicit',
                           'spotify_popularity',
                           'comment',
                           'rating',
                           'last_played_timestamp',
                           'genre',
                           'play_count']

    def add_track(self, track):
        model = {}
        for key in self.track_keys:
            try:
                model[key] = track[key]
            except:
                model[key] = ''
        id = hashlib.md5()
        id.update(model['title'].encode('utf-8'))
        id.update(model['album'].encode('utf-8'))
        id.update(model['artist'].encode('utf-8'))
        model['id'] = id.hexdigest()
        if model['id'] not in self.tracks:
            self.tracks.add(model['id'])
            self.library.append(model)

    def write_csv(self, outfile):
        with open(outfile, 'w', encoding = 'utf-8') as f:
            fieldnames = self.track_keys + ['id']
            writer = csv.DictWriter(f, fieldnames = fieldnames)
            writer.writeheader()
            sorted_library = sorted(self.library, key=operator.itemgetter('artist', 'album', 'track_number'))
            for row in sorted_library:
                writer.writerow(row)

    def find_diffs(self, other_library):
        diff_library = MusicLibrary()
        diff_tracks = self.tracks - other_library.tracks
        for track in self.library:
            if track['id'] in diff_tracks:
                diff_library.add_track(track)
        return diff_library
            
def gpm_login():
    client = Mobileclient()
    oauth = client.perform_oauth(open_browser=True)
    client.oauth_login(Mobileclient.FROM_MAC_ADDRESS,
                       oauth_credentials = oauth,
                       locale = 'en_US')
    if client.is_authenticated():
        print('👌')
    return client

def gpm_get_all_songs(client):
    while not client.is_authenticated():
        print('Your client is no longer authenticated. Reauthorizing...')
        client = gpm_login()
    gpm_library = client.get_all_songs()
    return gpm_library

def gpm_transform(gpm_export):
    music_library = MusicLibrary()
    for song in gpm_export:
        song_model = {}
        # Google's response is finicky and doesn't always have all the columns
        for col in GPM_EXPORT_COLS:
            try:
                song_model[col] = song[col]
            except:
                song_model[col] = ''
        song_model['release_date'] = song_model.pop('year')
        song_model['creation_timestamp'] = song_model.pop('creationTimestamp')
        song_model['last_played_timestamp'] = song_model.pop('recentTimestamp')
        song_model['album_artist'] = song_model.pop('albumArtist')
        song_model['track_number'] = song_model.pop('trackNumber')
        song_model['play_count'] = song_model.pop('playCount')
        song_model['duration_ms'] = song_model.pop('durationMillis')
        music_library.add_track(song_model)
    return music_library

def spotify_login(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET):
    SPOTIFY_REDIRECT_URI = 'http://localhost/'
    SPOTIFY_SCOPE = 'user-library-read'
    username = input('Spotify username: ')
    token = util.prompt_for_user_token(username,
                                       SPOTIFY_SCOPE,
                                       client_id=SPOTIFY_CLIENT_ID,
                                       client_secret=SPOTIFY_CLIENT_SECRET,
                                       redirect_uri=SPOTIFY_REDIRECT_URI)
    spotify = spotipy.Spotify(auth = token)
    return spotify

def spotify_get_all_songs(client):
    tracks = []
    offset = 0
    downloading = True
    while downloading:
        print('Downloading tracks ' + str(offset) + ' through ' + str(offset + 49))
        this_set = client.current_user_saved_tracks(limit = 50, offset = offset)
        for track in this_set['items']:
            tracks.append(track)
        offset += 50
        if len(this_set['items']) == 0:
            downloading = False
        else:
            time.sleep(1)
    return tracks

def spotify_transform(spotify_export):
    spotify_library = MusicLibrary()
    for track in spotify_export:
        model = {
            'creation_timestamp': track['added_at'],
            'album': track['track']['album']['name'],
            'album_artist': ' and '.join([a['name'] for a in track['track']['album']['artists']]),
            'release_date': track['track']['album']['release_date'],
            'artist': ' and '.join([a['name'] for a in track['track']['artists']]),
            'duration_ms': track['track']['duration_ms'],
            'explicit': track['track']['explicit'],
            'title': track['track']['name'],
            'popularity': track['track']['popularity'],
            'track_number': track['track']['track_number']
            }
        spotify_library.add_track(model)
    return spotify_library

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('-c', '--compare',
                        help = 'Creates two CSV files showing tracks that are in Spotify but missing from GPM and vice versa.',
                        action = 'store_true')
    parser.add_argument('-g', '--gpm',
                        action = 'store_true',
                        help = 'Write CSV file of GPM library.')
    parser.add_argument('-s', '--spotify',
                        action = 'store_true',
                        help = 'Write CSV file of Spotify library.')
    parser.add_argument('-o', '--outdir',
                        default = '',
                        type = str,
                        help = 'Directory to write CSV files.')
    args = parser.parse_args()

    # See if we need to deal with GPM
    if args.compare or args.gpm:
        print('Logging into GPM...')
        client = gpm_login()
        print('Getting your GPM library...')
        gpm_export = gpm_get_all_songs(client)
        print('Building a model of your GPM library...')
        gpm_library = gpm_transform(gpm_export)

    if args.gpm:
        gpm_outfile = os.path.join(os.path.expanduser(args.outdir), 'google_play_music_export.csv')
        print('Writing ' + gpm_outfile + '...')
        gpm_library.write_csv(gpm_outfile)
        print('Wrote ' + gpm_outfile)

    # See if we need to deal with Spotify
    if args.compare or args.spotify:
        print('Logging into Spotify...')
        spotify = spotify_login(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
        print('Getting your Spotify library...')
        spotify_export = spotify_get_all_songs(spotify)
        print('Building a model of your Spotify library...')
        spotify_library = spotify_transform(spotify_export)

    if args.compare:
        print('Finding unique Spotify tracks...')
        spotify_unique = spotify_library.find_diffs(gpm_library)
        spotify_unique_outfile = os.path.join(os.path.expanduser(args.outdir), 'spotify_unique_tracks.csv')
        print('Writing ' + spotify_unique_outfile)
        spotify_unique.write_csv(spotify_unique_outfile)

        print('Finding unique GPM tracks...')
        gpm_unique = gpm_library.find_diffs(spotify_library)
        gpm_unique_outfile = os.path.join(os.path.expanduser(args.outdir), 'gpm_unique_tracks.csv')
        print('Writing ' + gpm_unique_outfile)
        gpm_unique.write_csv(gpm_unique_outfile)

    if args.spotify:
        spotify_outfile = os.path.join(os.path.expanduser(args.outdir), 'spotify_export.csv')
        print('Writing ' + spotify_outfile + '...')
        spotify_library.write_csv(spotify_outfile)
