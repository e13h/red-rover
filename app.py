import os
from flask import Flask, render_template, request, session, redirect, url_for
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)
app.secret_key = bytes(os.getenv('SECRET_KEY'), 'utf-8')


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
    if 'web_playback_sdk_access_token' in session and 'web_api_access_token' in session:
        return redirect(url_for('player'))
    if refresh_token_is_valid():
        return redirect(url_for('player'))
    return render_template('sign_in_with_spotify.html')

def refresh_token_is_valid() -> bool:
    if 'spotify_refresh_token' not in session:
        return False
    return False

@app.route('/spotify-callback', methods=['GET', 'POST'])
def spotify_auth_callback():
    """Handle Spotify authentication response"""
    if request.method == 'POST':
        session['web_playback_sdk_access_token'] = request.form['web_playback_sdk_access_token']
        session['web_api_access_token'] = request.form['web_api_access_token']
        return redirect(url_for('index'))
    # if response contains an error
    #   point to spotify_auth
    # save token
    # point to player
    pass

@app.route('/player')
def player():
    """Render the player"""
    if ('site_access_token' not in session
        or 'web_playback_sdk_access_token' not in session
        or 'web_api_access_token' not in session):
        return redirect(url_for('index'))
    # if Spotify refresh token doesn't exist
    #   point back to spotify auth
    return render_template(
        'player.html',
        web_playback_sdk_access_token=session['web_playback_sdk_access_token'],
        web_api_access_token=session['web_api_access_token'])

@app.route('/reset')
def reset():
    session.pop('site_access_token', None)
    session.pop('web_playback_sdk_access_token', None)
    session.pop('web_api_access_token', None)
    return redirect(url_for('index'))
