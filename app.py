from flask import Flask, render_template, request
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if len(request.form) > 0:
        play_request = {
            'init_access_token': request.form['init_access_token'],
            'playback_access_token': request.form['playback_access_token'],
            'track_id': request.form['track_id'],
        }
        return render_template('init.html', play_request=play_request)
    return render_template('init.html')
