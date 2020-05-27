// Possible game states, mirroring backend gamestates.py
GAME_STATES = {
    "WAITING_IN_LOBBY": "Waiting in lobby",
    "READY": "Ready",
    "LOADING": "Loading",
    "GUESSING": "Guessing",
    "POST_ANSWERS": "Post answers",
    "RESULTS": "Results",
    "VICTORY": "Victory",
};

$(document).ready(function() {
    /**
     * Quiz variables
     * @type {HTMLAudioElement,number,string,boolean}
     */
    let audioElement = document.createElement('audio'),
        volume = 0.3,
        //slider = document.getElementById("volume-slider"),
        socketUrl = 'ws://' + window.location.host + '/ws/quiz' + window.location.pathname,
        gameState = GAME_STATES.WAITING_IN_LOBBY,
        pause = false,
        messageCount = 0,
        ready = false;
    audioElement.muted = true;

    /**
     * jQuery selectors
     * @type {jQuery.fn.init|jQuery|HTMLElement}
     */
    const gameContainer =  $("#game-container"),
        readyButtonContainer = $("#readybutton-container"),
        readyButton = $("#ready-button"),
        readySpan = $("#ready"),
        artistSpan = $("#artist"),
        titleSpan = $("#title"),
        coverSpan = $("#track-cover"),
        userInput = $("#playerinput"),
        timer = $("#current-time"),
        roundSpan = $("#current-round"),
        pauseButton = $('#pause'),
        volumeSlider = $("#volume"),
        gameSettingsButton = $("#game-settings-button"),
        settingsForm = $("#game-settings-form"),
        gameSettingsRounds = $("#game-settings-rounds"),
        gameSettingsPrivate = $("#game-settings-private"),
        gameSettingsPassword = $("#game-settings-password"),
        gameSettingsWords = $("#game-settings-words");

    console.log(socketUrl);
    const socket = new WebSocket(socketUrl);

    /**
     * Set up the volume slider.
     */
    volumeSlider.slider({
        orientation: "vertical",
        min: 0,
        max: 100,
        value: 50,
        range: "min",
        slide: function(event, ui) {
            setVolume(ui.value / 100);
        }
    });

    /**
     * Function to change the player volume.
     * @param myVolume Between 0 and 100.
     */
    function setVolume(myVolume) {
        audioElement.volume = myVolume;
        volume = myVolume;
    }


    /**
     * When the player is ready, set it up and play the song.
     */
    audioElement.addEventListener("canplay",function(){
        //timer.text(audioElement.duration);
        //socket.send("canplay");
        this.volume = volume;
        audioElement.muted = false;
        audioElement.play().then(r => {}); //TODO handle end of playing
    });

    /**
     * Update timer according to audio element.
     */
    audioElement.addEventListener("timeupdate",function(){
        timer.text(Math.floor(31-audioElement.currentTime));
    });

    /**
     * On click on the pause button, toggle between paused and unpaused and notify the server.
     */
    pauseButton.click(function() {
        if(!pause)
            audioElement.pause();
        else
            audioElement.play();
        pause = !pause;
        let infos = pause ? "PAUSE" : "RESUME";
        console.log(infos);
        socket.send(infos);
    });

    /*$('#restart').click(function() {
        audioElement.currentTime = 0;
    });
    audioElement.addEventListener('ended', function() {
            this.play();
    }, false);*/

    /**
     * Toggle ready status on view and notify server.
     */
    readyButton.click(function() {
        if (gameState === GAME_STATES.WAITING_IN_LOBBY) {
            ready = !ready;
            let infos = ready ? "READY" : "UNREADY";
            socket.send(infos);
        } else {
            socket.send("JOIN")
        }
    });

    // TODO Debug
    socket.onopen = function open() {
      console.log('WebSockets connection created.');
    };

    /**
     * Updates players info, mostly used for updating points, based on the game info given.
     * @param gameInfo Dict with game information.
     */
    function updatePlayers(gameInfo) {
        let userhtml = "";
        gameInfo.players.forEach(function(p, i) {
            let divClass = $("#user-menu").text().startsWith(p.user.username) ? "box featured" : "box";
            userhtml += "<div class=\"col-lg-" + String(Math.floor(12/gameInfo.players.length)) + " col-md-6 mb-md-4\">" +
                    "<div class=\"" + divClass + "\" data-aos=\"zoom-in\">" +
                        (p.answer !== "" ? "<h4 id=\"playeranswer\">" + p.answer + "</h4>" : "") +
                        "<h3>" + p.user.username + "</h3>" +
                        "<h4 id=\"userpoints\">" + String(p.points) + "<span> point" + (p.points === 1 ? "" : "s") + "</span></h4>" +
                    "</div>" +
                "</div>";
            $("#user-scores").html(userhtml);
        });

    }

    settingsForm.submit(function() {
        let settings = {
            rounds: gameSettingsRounds.val(),
            private: gameSettingsPrivate.is(":checked"),
            password: gameSettingsPassword.val(),
            game_type: $("#game-settings-game_type option:selected").text(),
            genre: $("#game-settings-genre option:selected").text(),
            words: gameSettingsWords.val(),
        };
        socket.send("SETTINGS:" + JSON.stringify(settings));
        return false;
    });

    gameSettingsButton.click(function() {
        socket.send("REQUEST SETTINGS");
    });

    /**
     * Just hides one element and shows another, to clean up code.
     * @param toHide Element to hide.
     * @param toShow Element to show
     */
    function hideShow(toHide, toShow) {
        toHide.hide();
        toHide.attr("class", "container invisible");
        toShow.show();
        toShow.attr("class", "container");
    }

    // On received websocket message
    socket.onmessage = function message(event) {
        // Parse de incoming data
        let data = JSON.parse(event.data);

        if (typeof data.private != "undefined") {
            gameSettingsRounds.val(data.rounds);
            gameSettingsPrivate.prop("checked", data.private);
            $("#game-settings-game_type option[text=\"" + data.game_type + "\"]").prop("selected", "selected");
            $("#game-settings-genre option[text=\"" + data.genre + "\"]").prop("selected", "selected");
            gameSettingsWords.val(data.words);

        } else {
            let gameInfo = JSON.parse(data),
                track = gameInfo.track;
            console.log(gameInfo); // TODO just for debug
            gameState = gameInfo.game_state;

            if (gameState !== GAME_STATES.WAITING_IN_LOBBY && messageCount === 0) { // Client must interact for autoplay to work
                readySpan.text("Join active game");
            } else {

                // State machine
                switch (gameState) {
                    case GAME_STATES.WAITING_IN_LOBBY:
                        hideShow(gameContainer, readyButtonContainer);
                        updatePlayers(gameInfo);
                        let text = !ready ? "Ready up" : "Unready";
                        readySpan.text(text);
                        break;

                    case GAME_STATES.READY:
                        hideShow(gameContainer, readyButtonContainer);
                        break;

                    case GAME_STATES.LOADING:
                        hideShow(gameContainer, readyButtonContainer);
                        readyButton.text("LOADING..."); //TODO show loading animation
                        hideShow(gameContainer, readyButtonContainer);
                        break;

                    case GAME_STATES.GUESSING:
                        hideShow(readyButtonContainer, gameContainer);
                        updatePlayers(gameInfo);
                        if (gameInfo.state_change || messageCount === 1) {
                            console.log("state change: " + gameInfo.state_change);
                            roundSpan.text("Round " + String(gameInfo.round) + "/" + String(gameInfo.total_rounds));
                            artistSpan.html("¿¿¿¿¿¿");
                            titleSpan.html("??????");
                            coverSpan.html("<img src=\"" + track.album.cover + "\" alt=\"cover\"/>");
                            audioElement.setAttribute('src', track.download_url);
                            coverSpan.css({
                                "-webkit-filter": "blur(50px)",
                                "filter": "blur(50px)"
                            });
                        }
                        break;

                    case GAME_STATES.POST_ANSWERS:
                        //TODO show loading animation
                        hideShow(readyButtonContainer, gameContainer);
                        let userAnswer = userInput.val();
                        userInput.val("");
                        socket.send("ANSWER:" + (userAnswer === undefined ? "" : userAnswer));
                        break;

                    case GAME_STATES.RESULTS:
                        hideShow(readyButtonContainer, gameContainer);
                        updatePlayers(gameInfo);
                        if (gameInfo.state_change || messageCount === 1) {
                            artistSpan.html(track.artists[0].name);
                            titleSpan.html(track.title);
                            coverSpan.html("<img src=\"" + track.album.cover + "\" alt=\"cover\"/>");
                            $({blurRadius: 50}).animate({blurRadius: 0}, {
                                duration: 2000,
                                easing: 'swing',
                                step: function () {
                                    coverSpan.css({
                                        "-webkit-filter": "blur(" + this.blurRadius + "px)",
                                        "filter": "blur(" + this.blurRadius + "px)"
                                    });
                                }
                            });
                            audioElement.setAttribute('src', track.download_url);
                            setTimeout(() => {
                                console.log("animated");
                            }, 2000);
                            coverSpan.css({
                                "-webkit-filter": "blur(0px);",
                                "filter": "blur(0px);"
                            });
                        }
                        //$("#score-username").html("6");
                        break;

                    default: // This should never happen
                        console.log("PLZ TO HELP");
                        console.log(gameState);
                        break;
                }
            }
        }
        messageCount++;
    };

    document.ws = socket; // TODO debug
    /*if (socket.readyState === WebSocket.OPEN) {
      socket.onopen();
    }*/
});

/*$( window ).on("unload", function(e) {
    const socket = new WebSocket(
            'ws://'
            + window.location.host
            + '/ws/quiz'
            + window.location.path
    );
    console.log("DISCONNECTED");
    socket.close();
});*/
