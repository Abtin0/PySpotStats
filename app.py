from flask import Flask, render_template, url_for, redirect, request, g
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)

# Environment variables for Spotify credentials
client_id = os.environ.get("PYSPOTSTATS_CLIENT_ID")
client_secret = os.environ.get("PYSPOTSTATS_CLIENT_SECRET")
redirect_uri = "http://localhost:5000/callback"
scope = "playlist-read-private,streaming,user-read-playback-state,user-top-read,user-library-read"

# Directory to store the cache
CACHE_DIR = ".spotify_cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# File-based caching for SpotifyOAuth
cache_path = os.path.join(CACHE_DIR, "token_cache")
oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    cache_path=cache_path,
    show_dialog=True,
)

sp = Spotify(auth_manager=oauth)


@app.before_request
def variables():
    g.index = url_for("index")
    g.get_playlists = url_for("get_playlists")
    g.login = url_for("login")


@app.route("/")
def index():
    if not oauth.validate_token(oauth.get_cached_token()):
        return render_template("index.html")
    return render_template("index.html")


@app.route("/login")
def login():
    auth_url = oauth.get_authorize_url()
    return render_template("login.html", auth_url=auth_url)


@app.route("/callback")
def callback():
    oauth.get_access_token(request.args["code"])
    return redirect(url_for("index"))


@app.route("/get_playlists")
def get_playlists():
    if not oauth.validate_token(oauth.get_cached_token()):
        auth_url = oauth.get_authorize_url()
        return render_template("login.html", auth_url=auth_url)
    playlists = sp.current_user_playlists()
    playlists_info = []
    for pl in playlists['items']:
        if pl and 'name' in pl and pl['name']:
            playlists_info.append((pl['name'], pl['external_urls']['spotify']))

    return render_template("get_playlists.html", playlists_info=playlists_info)


@app.route("/current")
def current():
    if not oauth.validate_token(oauth.get_cached_token()):
        return redirect(url_for("login"))  # Redirect to login if the token is invalid

    track = sp.currently_playing()
    if track is None:
        return "No track is currently playing."
    return track  # Or render it in a template if you prefer


@app.route("/top_artists")
def top_artists():
    if not oauth.validate_token(oauth.get_cached_token()):
        return redirect(url_for("login"))

    short_list = []
    for artist in sp.current_user_top_artists(time_range='short_term')["items"]:
        name = artist["name"]
        image = artist["images"][0]["url"]
        short_list.append((name, image))

    med_list = []
    for artist in sp.current_user_top_artists(time_range='medium_term')["items"]:
        name = artist["name"]
        image = artist["images"][0]["url"]
        med_list.append((name, image))

    long_list = []
    for artist in sp.current_user_top_artists(time_range='long_term')["items"]:
        name = artist["name"]
        image = artist["images"][0]["url"]
        long_list.append((name, image))

    return render_template("top_artists.html", short=short_list, med=med_list, long=long_list)


@app.route("/logout")
def logout():
    # Clear the cache by deleting the file
    if os.path.exists(cache_path):
        os.remove(cache_path)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)

