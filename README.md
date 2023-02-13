# Raspberry Pi Spotify Player
Code for NFC based spotify player. All you need is a RC522 reader soldered to any raspberry pi (many tutorials on this online).

- `configure-spotify.py` - Queries Spotify API for access token. Only need to do this through CLI once.
- `player.py` - Main player function. 

It supports classical read/write `RFID` tags, and secure `NTAG`s. `NTAG`s (similar to those used in amiibo) are encrypted, so instead the pi stores the encrypted tag ID to memory, rather than writing to the tag.

## Configuring Your Pi
### 1. Install and configure

First clone the repo and add your dependences (you will need Python and Pip):

```
git clone [this repo]
cd [this repo]
pip install -r requirements.txt
```

Next, you will need to create a [developer key](https://developer.spotify.com/dashboard) for your spotify account. When creating the key, make sure to set your Redirect URIs to `http://localhost:8080` and `http://localhost:8888/callback`

In the main folder, create a `spotify_config.json` file (`touch spotify_config.json & nano spotify_config.json`) in this format:

```
{
    "CLIENT_ID": [client id from spotify],
    "CLIENT_SECRET": [client secret from spotify],
    "DEVICE_ID": [desired device id if you would play from one device, None if using current device],
    "COUNTRY_CODE": "US",
    "SCOPE": [
        "user-read-playback-state", 
        "user-modify-playback-state", 
        "user-read-recently-played",
        "user-top-read",
        "playlist-read-private"
    ],
    "TAG_TYPE": "NTAG"
}
```

Now run `configure-spotify.py`, this will give a URL which will allow you to activate the device. If this is successful, you can use the player:

```
python3 player.py
```

Once you clone the repo and get `player.py` working, there's a couple extra things that will make the player work a bit better:

### 2. Network configuration

At Georgia Tech, I had to first set up my Pi by connecting to a LAN, then to the campus wifi. You can modify the Pi wifi setup with:

`sudo nano /etc/wpa_supplicant/wpa_supplicant.conf`

Here's what my wpa configuration looks like with multiple networks, higher = perferred. This allows the pi to default to campus wifi, but will connect back to my computer if it doesn't work.

```
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US

network={
    ssid=[network name 1]
    psk=[password]
    priority=1
}

network={
    ssid=[network name]
    psk=[password]
    priority=2
}
```

Here's a couple useful commands as well:

```
wpa_cli -i wlan0 list_networks # List available networks
wpa_cli -i wlan0 select_network 1 # Select a different network
```

### 3. Run at startup
You want this to run headless, and be resistent to turning on / off, wifi outages, etc. This is first done by simply ignoring exceptions in the code, but we also want `player.py` to run at startup. We will do this using `rc.local`. 

First make sure `rc.local` is executable by root:

```
sudo chmod 777 /etc/rc.local
```

Then modify (`sudo nano /etc/rc.local`) to add this line to run `player.py` using the default `pi` user. We will also export output to a log file:

```
sudo -H -u pi /usr/bin/python3 /home/pi/spotify-rfid/player.py & > /home/pi/player-log.txt 2>&1 &
```

Now if you `sudo reboot`, the player function should run automatically! You can check this either by seeing whether the player process is running or by whether the `rc-local` service is active.

```
ps aux | grep player.py
systemctl status rc-local.service
```
