import time
import os
from enum import Enum
from typing import Callable

from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for
import spotipy
from spotipy.cache_handler import CacheHandler
from spotipy.oauth2 import SpotifyPKCE, SpotifyStateError
from spotipy.exceptions import SpotifyException

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


class Command(Enum):
    PLAY = 'play'
    PAUSE = 'pause'
    SKIP = 'skip'
    PREVIOUS = 'previous'

    def label(self):
        return str(self.value).title()

    def route(self):
        return str(self.value).lower()

    def pair(self):
        return self.label(), self.route()

    @classmethod
    def all(cls):
        return cls.PREVIOUS, cls.SKIP


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
    if not site_access_token_is_valid():
        return redirect(url_for('coming_soon'))
    if not spotify_access_token_is_valid():
        return sign_in_with_spotify()
    access_token = spotify_cache_handler.get_cached_token()['access_token']
    commands = {command.route(): command.label() for command in Command.all()}
    top_tracks = get_top_tracks()
    return render_template(
        'player.html',
        access_token=access_token,
        commands=commands,
        tracks=enumerate(top_tracks),
    )


def get_top_tracks(limit=5, time_range="short_term") -> dict:
    result = sp.current_user_top_tracks(limit=limit, time_range=time_range)
    top_tracks = [
        dict(
            name=track["name"],
            image=track["album"]["images"][-1]["url"],
            artist=track["artists"][0]["name"],
            uri=track["uri"],
        )
        for track in result["items"]
    ]
    return top_tracks


def site_access_token_is_valid() -> bool:
    if 'site_access_token' not in session:
        return False
    valid_site_access_tokens = os.getenv('SITE_ACCESS', '').split()
    if session['site_access_token'] not in valid_site_access_tokens:
        session.pop('site_access_token', None)
        return False
    return True


def spotify_access_token_is_valid() -> bool:
    if sp.auth_manager.validate_token(spotify_cache_handler.get_cached_token()) is None:
        return False
    return True


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
    return redirect(url_for('index'))


@app.route('/reset')
def reset():
    session.pop('site_access_token', None)
    session.pop('web_playback_sdk_access_token', None)
    session.pop('web_api_access_token', None)
    session.pop('spotify_token_info', None)
    return redirect(url_for('index'))


@app.route(f'/spotify/{Command.PLAY.route()}/<track_uri>')
def spotify_command_play(track_uri: str = None):
    uris = [track_uri] if track_uri else None
    device_id = request.args.get('device_id', None)
    return spotify_player_action(sp.start_playback, lambda: True, uris=uris, device_id=device_id)


@app.route(f'/spotify/{Command.PAUSE.route()}')
def spotify_command_pause():
    return spotify_player_action(sp.pause_playback, lambda: not sp.current_playback().get("is_playing", True))


@app.route(f'/spotify/{Command.SKIP.route()}')
def spotify_command_skip():
    return spotify_player_action(sp.next_track, lambda: True)


@app.route(f'/spotify/{Command.PREVIOUS.route()}')
def spotify_command_previous():
    return spotify_player_action(sp.previous_track, lambda: True)


def spotify_player_action(action: Callable, verification: Callable, **action_kwargs: dict) -> dict:
    TIMEOUT_SEC = 3.0
    DELAY_BETWEEN_CALLS_SEC = 0.25
    MAX_NUM_TRIES = int(TIMEOUT_SEC / DELAY_BETWEEN_CALLS_SEC)
    try:
        if len(action_kwargs) > 0:
            action(**action_kwargs)
        else:
            action()
        num_tries = 0
        while num_tries < MAX_NUM_TRIES and not verification():
            time.sleep(DELAY_BETWEEN_CALLS_SEC)
            num_tries += 1
        if num_tries >= MAX_NUM_TRIES and not verification():
            return dict(success=False, reason="timed out")
        return dict(success=True)
    except SpotifyException as e:
        if e.http_status == 404:
            reason = "device not found"
        elif e.http_status == 403:
            reason = "user is non_premium"
        elif e.http_status == 429:
            retry_after = e.headers.get("Retry-After", None)
            reason = f"rate limited, retry after {retry_after}"
        else:
            reason = "unknown"
        return dict(success=False, reason=reason)
