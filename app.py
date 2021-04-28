import os
from flask import Flask, render_template, request, session, redirect, url_for
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)
app.secret_key = bytes(os.getenv('SECRET_KEY'), 'utf-8')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        play_request = {
            'init_access_token': request.form['init_access_token'],
            'playback_access_token': request.form['playback_access_token'],
            'track_id': request.form['track_id'],
        }
        return render_template('init.html', play_request=play_request)
    if 'username' in session:
        return render_template('init.html', username=session.get('username', None))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))
