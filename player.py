#!/usr/bin/env python
from mfrc522 import SimpleMFRC522, MFRC522
import RPi.GPIO as GPIO
import spotipy
import json
import os
import sys
from spotipy.oauth2 import SpotifyOAuth
from time import sleep

os.chdir(os.path.dirname(sys.argv[0]))

# Load spotify configuration
with open('spotify_config.json', 'r') as f:
    config = json.load(f)

# Load ntag mapping file
with open('tag_mapping.json', 'r') as f:
    ntag_mapping = json.load(f)

# Specify device ID to force a device switch everytime a song is played.
# Useful if you want the pi to take over playback
# config['DEVICE_ID'] = "8c90e67c90a93592672e4a0d4bb5f5c3cf130a32" # David's laptop Device ID
config['DEVICE_ID'] = None

# config['TAG_TYPE'] may be RFID or NTAG. Set to NTAG if using encrypted
# NFC tags, such that the tag values are stored on the pi, rather than
# writing the contents of the NFC tag.

def setup():
    if config['TAG_TYPE'] == "NTAG":
        reader = MFRC522()
    else:
        reader = SimpleMFRC522()

    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=config['CLIENT_ID'],
            client_secret=config['CLIENT_SECRET'],
            redirect_uri="http://localhost:8080",
            scope=''.join(x+',' for x in config['SCOPE'])[:-1],
            open_browser=False
        ))
    return reader, sp

def save_mapping_to_file(new_ntag_mapping):
    with open('tag_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(new_ntag_mapping, f, ensure_ascii=False, indent=4)

def pause(sp):
    sp.pause_playback()

def skip_track(sp):
    sp.next_track()

def switch_context(sp, context_uri):
    sp.shuffle(True)
    # print(f'Playing {context_uri} on {config['DEVICE_ID']}')
    if 'track' in context_uri:
        sp.start_playback(device_id=config['DEVICE_ID'], uris=[f'{context_uri}'])
    else:
        sp.start_playback(device_id=config['DEVICE_ID'], context_uri=f'{context_uri}')

def write_card(reader, sp):
    # Get the currently playing playlist id
    current_playback = sp.current_playback()
    if current_playback['context'] is not None:
        context_uri = current_playback['context']['uri']
    elif 'track' in current_playback['currently_playing_type']:
        context_uri = current_playback['item']['uri']
    else:
        print(f"Content: {current_playback} not supported, skipping ...")
        return

    # Stop playback
    sp.pause_playback()

    # Write to card
    print("Writing... " + context_uri)

    print("Searching for non-write card")
    found = False
    while found == False:
        print("Waiting for RFID scan...")
        if config['TAG_TYPE'] == "NTAG":
            buf = read_ntag(reader)
            if buf in ntag_mapping.keys():
                text = ntag_mapping[buf]
            else:
                text = ''
        else:
            id_, text = reader.read()
        text = text.replace(' ', '')
        print(f"Read: {text}") # {id_}
        if 'admin:write' not in text:
            found = True
            if config['TAG_TYPE'] == "NTAG":
                ntag_mapping[buf] = context_uri
                save_mapping_to_file(ntag_mapping)
            else:
                reader.write(context_uri)
            print("Written!")

    # Resume playback
    sp.start_playback()

def read_ntag(reader):
    while True:
        status, _ = reader.MFRC522_Request(reader.PICC_REQIDL)
        if status != reader.MI_OK:
            sleep(0.1)
            continue
        status, backData = reader.MFRC522_Anticoll()
        buf = reader.MFRC522_Read(0)
        reader.MFRC522_Request(reader.PICC_HALT)
        return str(sum(buf))

def scan_card(reader, sp):
    print("Waiting for RFID scan...")

    if config['TAG_TYPE'] == "NTAG":
        buf = read_ntag(reader)
        text = ntag_mapping[buf]
    else:
        id_, text = reader.read()

    text = text.replace(' ', '')
    print(f"Read: {text}") #{id_}

    # admin:write will write a new card
    if 'admin' in text:
        if 'write' in text:
            write_card(reader, sp)
    else:
        switch_context(sp, text)

while True:
    try:
        reader, sp = setup()

        print(f"Using device {config['DEVICE_ID']}")
        sp.repeat('context')
        
        while True:
            scan_card(reader, sp)

    # Print & skip any errors
    except Exception as e:
        print(e)
        pass

    finally:
        print("Cleaning  up...")
        GPIO.cleanup()
