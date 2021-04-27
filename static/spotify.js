async function spotifyInit(access_token) {
    p = new Promise((resolve, reject) => {
        window.onSpotifyWebPlaybackSDKReady = () => {
            const player = new Spotify.Player({
                name: 'Web Playback SDK Quick Start Player',
                getOAuthToken: cb => { cb(access_token); }
            });

            // Error handling
            player.addListener('initialization_error', ({ message }) => { reject(message); });
            player.addListener('authentication_error', ({ message }) => { reject(message); });
            player.addListener('account_error', ({ message }) => { reject(message); });
            player.addListener('playback_error', ({ message }) => { reject(message); });

            // Playback status updates
            player.addListener('player_state_changed', state => { console.log(state); });

            // Ready
            player.addListener('ready', ({ device_id }) => {
                console.log('Ready with Device ID', device_id);
                resolve([player, device_id]);
            });

            // Not Ready
            player.addListener('not_ready', ({ device_id }) => {
                console.log('Device ID has gone offline', device_id);
                reject('offline ' + device_id);
            });

            // Connect to the player!
            player.connect();
        };
    });
    return p;
}

function playTrack(track_id, device_id, access_token) {
    fetch(`https://api.spotify.com/v1/me/player/play?device_id=${device_id}`, {
        method: 'PUT',
        body: JSON.stringify({ context_uri: track_id }),
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${access_token}`
        },
    })
        .then(console.log);
}
