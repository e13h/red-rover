window.spotify_device_id = null;
window.spotify_player = null;
spotify_access_token = document.currentScript.getAttribute('access_token');

window.onSpotifyWebPlaybackSDKReady = () => {
    window.spotify_player = new Spotify.Player({
        name: 'Red Rover',
        getOAuthToken: cb => { cb(spotify_access_token); }
    });

    // Error handling
    window.spotify_player.addListener('initialization_error', ({ message }) => {
        console.error(message);
    });
    window.spotify_player.addListener('authentication_error', ({ message }) => {
        console.error(message);
    });
    window.spotify_player.addListener('account_error', ({ message }) => {
        console.error(message);
    });
    window.spotify_player.addListener('playback_error', ({ message }) => {
        console.error(message);
    });

    // Playback status updates
    window.spotify_player.addListener('player_state_changed', state => {
        console.log(state);
    });

    // Ready
    window.spotify_player.addListener('ready', ({ device_id }) => {
        console.log('Ready with Device ID', device_id);
        window.spotify_device_id = device_id;

        let play_button = document.getElementById('play-pause');
        play_button.addEventListener('click', () => {
            window.spotify_player.togglePlay().then(() => {
                console.log('toggled playback!');
            });
        });
        play_button.textContent = 'Play/Pause';
        play_button.disabled = false;
    });

    // Not Ready
    window.spotify_player.addListener('not_ready', ({ device_id }) => {
        console.log('Device ID has gone offline', device_id);
        window.spotify_device_id = null;
    });

    // Connect to the player!
    window.spotify_player.connect();
};

addEventListener('DOMContentLoaded', () => {
    for (const command of document.querySelectorAll('.command')) {
        command.addEventListener('click', defaultHandler);
    }
    for (const track of document.querySelectorAll('.track')) {
        track.addEventListener('click', defaultHandler);
    }
}, true);

function defaultHandler(event) {
    event.preventDefault(); // stop the button from submitting form (if any)
    let clickedButton = event.target;
    let command = clickedButton.value;
    runCommand(command);
}

function runCommand(command) {
    // Send the data to our server without reloading the page (AJAX)
    // Create a new request object and set up a handler for the response
    let request = new XMLHttpRequest();
    request.onload = () => {
        // We could do more interesting things with the response
        // or, we could ignore it entirely
        console.log(request.responseText);
    };
    request.open(
        'GET',
        '/spotify/' + command + '?device_id=' + window.spotify_device_id,
        true);
    request.send();
}
