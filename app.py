from flask import Flask, session, render_template, url_for, redirect, request
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)

client_id = os.environ.get("PYSPOTSTATS_CLIENT_ID")
client_secret = os.environ.get("PYSPOTSTATS_CLIENT_SECRET")
redirect_uri = "http://localhost:5000/callback"
scope = "playlist-read-private,streaming"

cache_handler = FlaskSessionCacheHandler(session)
oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True,
)

sp = Spotify(auth_manager=oauth)


@app.route("/")
def index():
    if not oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = oauth.get_authorize_url()
        return render_template("index.html", auth_url=auth_url)
    return redirect(url_for("get_playlists"))


@app.route("/callback")
def callback():
    oauth.get_access_token(request.args["code"])
    return redirect(url_for("get_playlists"))


@app.route("/get_playlists")
@app.route("/get_playlists")
def get_playlists():
    if not oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = oauth.get_authorize_url()
        return render_template("index.html", auth_url=auth_url)

    playlists = sp.current_user_playlists()
    playlists_info = []
    for pl in playlists['items']:
        if pl and 'name' in pl and pl['name']:  # Check if 'pl' is not None and has a 'name' field
            playlists_info.append((pl['name'], pl['external_urls']['spotify']))
    playlists_html = '<br>'.join([f'{name}: {url}' for name, url in playlists_info])

    return playlists_html



@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)

