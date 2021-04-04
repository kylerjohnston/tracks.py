# tracks.py

## Introduction
`tracks.py` is an application to track and compare your music libraries on Spotify and Google Play Music. You can use it to create CSV files documenting the tracks saved in your streaming libraries, and to compare your libraries on Spotify and GPM to find missing tracks.

It's most useful right now for creating a CSV file documenting all the tracks in your Spotify or GPM library. Because of variations in spelling ("Trigger Cut/Wounded-Knee at :17" on Spotify versus "Trigger Cut/Wounded Knee at :17" on GPM) and different track versions across reissues, remasters, compilations, etc., I need to tweak the comparison component to do more of a fuzzy search, but this becomes a philosophical exercise in figuring out how fuzzy two tracks have to match for me to consider them the same thing.

## Installation

### Dependencies
You will need these system packages installed (for Fedora, at least):
- python3-devel
- libxml2-devel
- libxslt-devel

You need to install these libraries:
- gmusicapi
- spotipy

Make a venv and install them:

``` shell
python -m venv venv/
source venv/bin/activate
pip install -r requirements.txt
```

### Authenticating to Spotify
If you need to connect to a Spotify account, you will need to create a Spotify authorization token by going to [the Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications) and clicking "Create a Client ID."

Add your client ID and client secret to the file `spotify_token.py`.

``` python
SPOTIFY_CLIENT_ID='your client id'
SPOTIFY_CLIENT_SECRET='your client secret'
```

## Usage

```
tracks.py is an application to track and compare your Spotify and Google Play
Music libraries.

optional arguments:
  -h, --help            show this help message and exit
  -c, --compare         Creates two CSV files showing tracks that are in
                        Spotify but missing from GPM and vice versa.
  -g, --gpm             Write CSV file of GPM library.
  -s, --spotify         Write CSV file of Spotify library.
  -o OUTDIR, --outdir OUTDIR
                        Directory to write CSV files.
```

Pretty simple. Common usages:

`tracks.py --gpm` generates a CSV file documenting all the tracks in your Google Play Music library.

`tracks.py --spotify` does the same for your Spotify library.

`tracks.py --compare` creates two CSV files documenting tracks unique to Spotify and GPM.

You could do something like `tracks.py --gpm --spotify --compare` to generate all of the above in one command.

