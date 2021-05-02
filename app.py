import os

from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for
import spotipy
from spotipy.cache_handler import CacheHandler
from spotipy.oauth2 import SpotifyPKCE, SpotifyStateError

load_dotenv()


app = Flask(__name__)
app.secret_key = bytes(os.getenv('SECRET_KEY'), 'utf-8')


class SessionCacheHandler(CacheHandler):
    """
    Handles reading and writing cached Spotify authorization tokens
    as browser cookies using flask.session.
    """

    def __init__(self):
        return None

    def get_cached_token(self):
        return session.get('spotify_token_info', None)

    def save_token_to_cache(self, token_info):
        session['spotify_token_info'] = token_info


SCOPES = [
    'user-read-recently-played',
    'user-top-read',
    'user-read-playback-position',
    'user-read-playback-state',
    'user-modify-playback-state',
    'user-read-currently-playing',
    'streaming',
    'playlist-read-private',
    'playlist-read-collaborative',
    'user-follow-read',
    'user-library-read',
    'user-read-email',
    'user-read-private',
]

spotify_cache_handler = SessionCacheHandler()
sp = spotipy.Spotify(auth_manager=SpotifyPKCE(
    scope=SCOPES, cache_handler=spotify_cache_handler))


@app.route('/')
def index():
    """Look for valid site access token"""
    if 'site_access_token' not in session:
        return redirect(url_for('coming_soon'))
    valid_site_access_tokens = os.getenv('SITE_ACCESS', '').split()
    if session['site_access_token'] not in valid_site_access_tokens:
        session.pop('site_access_token', None)
        return redirect(url_for('coming_soon'))
    return sign_in_with_spotify()


@app.route('/early-access', methods=['GET', 'POST'])
@app.route('/coming-soon', methods=['GET', 'POST'])
def coming_soon():
    if request.method == 'POST':
        session['site_access_token'] = request.form['site_access_token']
        return redirect(url_for('index'))
    return render_template('coming_soon.html')


def sign_in_with_spotify():
    """Check for Spotify refresh token.
    Handle Spotify authentication to get refresh token.
    """
    return redirect(sp.auth_manager.get_authorize_url())


@app.route('/spotify-callback', methods=['GET', 'POST'])
def spotify_auth_callback():
    """Handle Spotify authentication response"""
    state = request.args.get('state', None)
    if sp.auth_manager.state is not None and sp.auth_manager.state != state:
        raise SpotifyStateError(sp.auth_manager.state, state)
    error = request.args.get('error', None)
    if error:
        raise RuntimeError(error)
    code = request.args.get('code', None)
    sp.auth_manager.get_access_token(code=code, check_cache=True)
    return redirect(url_for('player'))


@app.route('/player')
def player():
    """Render the player"""
    if 'site_access_token' not in session:
        return redirect(url_for('index'))
    if sp.auth_manager.validate_token(spotify_cache_handler.get_cached_token()) is None:
        return sign_in_with_spotify()
    access_token = spotify_cache_handler.get_cached_token()['access_token']
    return render_template('player.html', access_token=access_token)


@app.route('/reset')
def reset():
    session.pop('site_access_token', None)
    session.pop('web_playback_sdk_access_token', None)
    session.pop('web_api_access_token', None)
    session.pop('spotify_token_info', None)
    return redirect(url_for('index'))
