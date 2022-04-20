import sys
import json
import time
import spotipy
import pandas as pd
from spotipy.oauth2 import SpotifyClientCredentials

client_id = 'be6c9bede21a427eb7bc36544b630d16'
client_secret = 'ca9edb0705264512900c60b7a7913efe'

client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def get_track_ids(path):
    with open(path) as f:
        js = f.read()
        challenge_set = json.loads(js)

        unique_tracks = set()
        unique_albums = set()
        unique_artists = set()
        total_tracks = 0
        for playlist in challenge_set["playlists"]:
            for track in playlist["tracks"]:
                unique_tracks.add(track["track_uri"][14:])
                unique_albums.add(track["album_uri"])
                unique_artists.add(track["artist_uri"])
                total_tracks += 1
        print("total playlists:", len(challenge_set["playlists"]))
        print("total tracks:   ", total_tracks)
        print("unique tracks:  ", len(unique_tracks))
        print("unique albums:  ", len(unique_albums))
        print("unique artists: ", len(unique_artists))
        return unique_tracks


def get_audio_features(track_ids, chunk_size):
    audio_features_list = []
    for i in range(0, len(track_ids), chunk_size):    
        try:
            track_id_list = track_ids[i:i+chunk_size]
            results = sp.audio_features(track_id_list)
            results = [dict({'id':'None'}) if v is None else v for v in results]
            for result in results:
                del result['track_href']
                del result['analysis_url']
                del result['type']
                del result['uri']
            audio_features_list.extend(results)
        except Exception as e:
            print(e)
            continue
    return audio_features_list

def get_tracks_data(track_ids, chunk_size):
    tracks_data_list = []
    single_track_dict = {}
    for i in range(0, len(track_ids), chunk_size):    
        try:
            track_id_list = track_ids[i:i+chunk_size]
            track_results = sp.tracks(track_id_list)
            for track in track_results['tracks']:    
                single_track_dict = {                                       
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'id': track['id'],
                    'artist_url': track['artists'][0]['external_urls']['spotify'],
                    'release_date': track['album']['release_date'],
                    'popularity':  track['popularity'],
                }
                tracks_data_list.append(single_track_dict)
        except Exception as e:
            print(e)
            continue
    return tracks_data_list

def get_tracks_genre(urls, chunk_size):
    genre_list = []
    single_artist_dict = {}
    for i in range(0, len(urls), chunk_size):    
        try:
            artist_url_list = urls[i:i+chunk_size]
            artist_results = sp.artists(artist_url_list)
            for artist in artist_results['artists']:  
                genres = artist['genres']
                if len(genres) == 0:
                    continue
                else:
                    genre = genres[0]      
                single_artist_dict = {                                       
                    'artist_url': artist['external_urls']['spotify'],
                    'genre': genre,
                }
                genre_list.append(single_artist_dict)
        except Exception as e:
            print(e)
            continue
    return genre_list

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract_data.py challenge_set.json")
    else:
        track_ids = list(get_track_ids(sys.argv[1]))
        tracks_data_list = get_tracks_data(track_ids, 50)

        artist_urls = [track['artist_url'] for track in tracks_data_list]
        tracks_genre_list = get_tracks_genre(artist_urls, 50)

        audio_features_list = get_audio_features(track_ids , 100)

        tracks_data_df = pd.DataFrame(tracks_data_list)
        tracks_data_df.dropna(inplace=True)

        genre_df = pd.DataFrame(tracks_genre_list)
        genre_df.dropna(inplace=True)

        audio_features_df = pd.DataFrame(audio_features_list)
        audio_features_df.dropna(inplace=True)

        tracks_data_df = tracks_data_df.merge(genre_df, on='artist_url', how='inner')
        tracks_data_df.drop(['artist_url'], axis=1, inplace=True)

        merged_df = tracks_data_df.merge(audio_features_df, on='id', how='inner')
        merged_df.dropna(inplace=True)
        merged_df.drop_duplicates(inplace=True)
        merged_df.to_csv('data.csv', sep=',', index=False)
