import spotipy
from spotipy.oauth2 import SpotifyOAuth
from time import sleep
import os
import json

# Set working directory to this file to SpotiPy can read .cache
os.chdir(os.path.dirname(__file__))

with open('spotify_config.json', 'r') as f:
    config = json.load(f)
config['DEVICE_ID'] = None

DAVID_SPOTIFY_USER_URI = "spotify:user:zqs13arexsn3y64e04fsfyqp9"

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=config['CLIENT_ID'],
        client_secret=config['CLIENT_SECRET'],
        redirect_uri="http://localhost:8080",
        scope=''.join(x+',' for x in config['SCOPE'])[:-1],
        open_browser=False
    ))

print(f'Available devices: {sp.devices()}', end='\n\n')

print(f"Using device {config['DEVICE_ID']}", end='\n\n')
sp.repeat('context')
sp.volume(100)

# sp.transfer_playback(device_id=config['DEVICE_ID'], force_play=False)

recentlyPlayed = sp.current_user_recently_played(limit=5)['items']
print(f"Last 5 played songs: {[x['track']['name'] + ':' + x['track']['uri'] for x in recentlyPlayed]}", end='\n\n')

print("Playing a song... ", end='')
sp.start_playback(device_id=config['DEVICE_ID'], context_uri='spotify:playlist:37i9dQZEVXcRiA1DVuNXSG')
print("Done!", end='\n\n')

topTracks = sp.current_user_top_tracks(time_range="short_term", limit=5)['items']
print("Top tracks:")
for track in topTracks:
    print(f"{track['name']} ({''.join([x['name'] + ', ' for x in track['artists']])[:-2]}) : {track['uri']}")

print("\nSome current playlists")
playlists = sp.current_user_playlists(limit=10)['items']
for playlist in playlists:
    print(f"{playlist['name']} by {playlist['owner']['display_name']} ({playlist['uri']})")
