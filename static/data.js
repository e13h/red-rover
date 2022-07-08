addEventListener('DOMContentLoaded', () => {
    for (const command of document.querySelectorAll('.form-new-mood-submit')) {
        command.addEventListener('click', (event) => {
            event.preventDefault(); // stop the button from submitting form (if any)
            let clickedButton = event.target;

            let request = new XMLHttpRequest();
            request.onload = () => {
                // We could do more interesting things with the response
                // or, we could ignore it entirely
                console.log(request.responseText);
            }
            request.open(
                'PUT',
                `/spotify/${command}?device_id=${window.spotify_device_id}`,
                true);
            request.send();
        });
    }
}, true);

// function defaultHandler(event) {
//     event.preventDefault(); // stop the button from submitting form (if any)
//     let clickedButton = event.target;
//     let command = clickedButton.value;
//     runCommand(command);
// }

// function runCommand(command) {
//     // Send the data to our server without reloading the page (AJAX)
//     // Create a new request object and set up a handler for the response
//     let request = new XMLHttpRequest();
//     request.onload = () => {
//         // We could do more interesting things with the response
//         // or, we could ignore it entirely
//         console.log(request.responseText);
//     };
//     request.open(
//         'GET',
//         `/spotify/${command}?device_id=${window.spotify_device_id}`,
//         true);
//     request.send();
// }