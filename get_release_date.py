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

def get_tracks_data(track_ids, chunk_size):
    tracks_data_list = []
    single_track_dict = {}
    for i in range(0, len(track_ids), chunk_size):    
        try:
            track_id_list = track_ids[i:i+chunk_size]
            track_results = sp.tracks(track_id_list)
            for track in track_results['tracks']:    
                single_track_dict = {                                       
                    'track_id': track['id'],
                    'release_date': track['album']['release_date'],
                }
                tracks_data_list.append(single_track_dict)
        except Exception as e:
            print(e)
            continue
    return tracks_data_list

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_release_date.py SpotifyFeatures.csv")
    else:
        df_kaggle = pd.read_csv(sys.argv[1])
        track_ids = list(set(df_kaggle['track_id']))
        tracks_data_list = get_tracks_data(track_ids, 50)

        tracks_data_df = pd.DataFrame(tracks_data_list)
        tracks_data_df.dropna(inplace=True)

        merged_df = tracks_data_df.merge(df_kaggle, on='track_id', how='left')
        merged_df.dropna(inplace=True)
        merged_df.drop_duplicates(inplace=True)
        print(df_kaggle.shape)
        print(merged_df.shape)
        merged_df.to_csv('data_kaggle.csv', sep=',', index=False)
