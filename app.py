from flask import Flask, render_template, url_for, redirect, request, g, session
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
load_dotenv()

# Environment variables for Spotify credentials
client_id = os.getenv("PYSPOTSTATS_CLIENT_ID")
client_secret = os.getenv("PYSPOTSTATS_CLIENT_SECRET")
redirect_uri = "http://localhost:5000/callback"
scope = "playlist-read-private,streaming,user-read-playback-state,user-top-read,user-library-read"

# Directory to store the cache
CACHE_DIR = ".spotify_cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Function to create user-specific SpotifyOAuth instance
def create_spotify_oauth():
    user_cache_path = os.path.join(CACHE_DIR, session['uuid'])
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        cache_path=user_cache_path,
        show_dialog=True,
    )

@app.before_request
def assign_session():
    g.index = url_for("index")
    g.get_playlists = url_for("get_playlists")
    g.login = url_for("login")
    g.top_artists = url_for("top_artists")
    if 'uuid' not in session:
        session['uuid'] = str(uuid.uuid4())

@app.route("/")
def index():
    oauth = create_spotify_oauth()
    if not oauth.validate_token(oauth.get_cached_token()):
        return render_template("index.html")
    return render_template("index.html")

@app.route("/login")
def login():
    oauth = create_spotify_oauth()
    auth_url = oauth.get_authorize_url()
    return render_template("login.html", auth_url=auth_url)

@app.route("/callback")
def callback():
    oauth = create_spotify_oauth()
    oauth.get_access_token(request.args["code"])
    return redirect(url_for("index"))


@app.route("/get_playlists")
def get_playlists():
    oauth = create_spotify_oauth()
    token_info = oauth.get_cached_token()
    if not oauth.validate_token(token_info):
        return redirect(url_for("login"))

    sp = Spotify(auth=token_info["access_token"])
    playlists = sp.current_user_playlists()
    playlists_info = []

    for pl in playlists['items']:
        if pl and 'name' in pl and pl['name']:
            image_url = pl['images'][0]["url"] if pl.get('images') and len(
                pl['images']) > 0 else "/static/images/default_playlist.jpg"
            playlists_info.append((pl['name'], pl['external_urls']['spotify'], image_url))

    return render_template("get_playlists.html", playlists_info=playlists_info)


@app.route("/current")
def current():
    oauth = create_spotify_oauth()
    token_info = oauth.get_cached_token()
    if not oauth.validate_token(token_info):
        return redirect(url_for("login"))
    sp = Spotify(auth=token_info["access_token"])
    track = sp.currently_playing()
    if track is None:
        return "No track is currently playing."
    return track

@app.route("/top_artists")
def top_artists():
    oauth = create_spotify_oauth()
    token_info = oauth.get_cached_token()
    if not oauth.validate_token(token_info):
        return redirect(url_for("login"))
    sp = Spotify(auth=token_info["access_token"])

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
    user_cache_path = os.path.join(CACHE_DIR, session.get('uuid', ''))
    if os.path.exists(user_cache_path):
        os.remove(user_cache_path)
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)


