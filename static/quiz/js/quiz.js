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
    let audioElement = document.createElement('audio'),
        volume = 0.3,
        slider = document.getElementById("volume-slider"),
        gameState = GAME_STATES.WAITING_IN_LOBBY,
        pause = false,
        ready = false;
    audioElement.muted = true;

    console.log(
            'ws://'
            + window.location.host
            + '/ws/quiz'
            + window.location.pathname
    );
    const socket = new WebSocket(
            'ws://'
            + window.location.host
            + '/ws/quiz'
            + window.location.pathname
        );

    $("#volume").slider({
        orientation: "vertical",
        min: 0,
        max: 100,
        value: 50,
        range: "min",
        slide: function(event, ui) {
            setVolume(ui.value / 100);
        }
    });

    function setVolume(myVolume) {
        audioElement.volume = myVolume;
        volume = myVolume;
    }

    //audioElement.addEventListener('ended', function() {
    //        this.play();
    //}, false);

    audioElement.addEventListener("canplay",function(){
        $("#timer").text(audioElement.duration-1);
        //socket.send("canplay");
        this.volume = volume;
        audioElement.muted = false;
        audioElement.play();
    });

    audioElement.addEventListener("timeupdate",function(){
        $("#currentTime").text(Math.floor(31-audioElement.currentTime));
    });

    $('#pause').click(function() {
        if(!pause)
            audioElement.pause();
        else
            audioElement.play();
        pause = !pause;
        let infos = pause ? "PAUSE" : "RESUME";
        console.log(infos);
        socket.send(infos);
    });

    $('#restart').click(function() {
        audioElement.currentTime = 0;
    });

    $('#ready-button').click(function() {
        ready = !ready;
        let infos = ready ? "READY" : "UNREADY";
        socket.send(infos);
    });

    socket.onopen = function open() {
      console.log('WebSockets connection created.');
      //socket.send("I have connected")
    };

    function updatePlayers(gameInfo) {
        let userhtml = "";
        for(let i = 0; i < gameInfo.num_players; i++) {
            userhtml += "<div class=\"col-lg-" + String(Math.floor(12/gameInfo.num_players)) + " col-md-6 mb-md-4\">" +
                    "<div class=\"box featured\" data-aos=\"zoom-in\">" +
                        "<h3>" + String(gameInfo.players[i].user.username) + "</h3>" +
                        "<h4>" + String(gameInfo.players[i].points) + "<span> point" + (gameInfo.players[i].points === 1 ? "" : "s") + "</span></h4>" +
                    "</div>" +
                "</div>";
            $("#user-scores").html(userhtml);
        }
    }

    socket.onmessage = function message(event) {
        let data = JSON.parse(event.data),
            gameInfo = JSON.parse(data),
            track = gameInfo.track;
        console.log(gameInfo); 
        gameState = gameInfo.game_state;

        switch (gameState) {
            case GAME_STATES.WAITING_IN_LOBBY:
                $("#game-container").hide();
                $("#readybutton-container").show();
                break;

            case GAME_STATES.READY:
                $("#game-container").hide();
                $("#readybutton-container").show();
                break;

            case GAME_STATES.LOADING:
                $("#game-container").show();
                $("#readybutton-container").hide();
                break;

            case GAME_STATES.GUESSING:
                $("#game-container").show();
                $("#readybutton-container").hide();
                updatePlayers(gameInfo);
                $("#artist").html("¿¿¿¿¿¿");
                $("#title").html("??????");
                $("#track-cover").html("<img src=\"" + track.album.cover + "\" alt=\"cover\"/>");
                audioElement.setAttribute('src', track.download_url);
                $('#track-cover').css({
                    "-webkit-filter": "blur(50px)",
                    "filter": "blur(50px)"
                });
                break;

            case GAME_STATES.POST_ANSWERS:
                $("#game-container").show();
                $("#readybutton-container").hide();
                userAnswer = $("#useranswer").val();
                $("#useranswer").val("");
                socket.send("ANSWER:" + userAnswer);
                break;

            case GAME_STATES.RESULTS:
                $("#game-container").show();
                $("#readybutton-container").hide();
                updatePlayers(gameInfo)
                $("#artist").html(track.artists[0].name);
                $("#title").html(track.title);
                $("#track-cover").html("<img src=\"" + track.album.cover + "\"/>");
                $({blurRadius: 50}).animate({blurRadius: 0}, {
                    duration: 2000,
                    easing: 'swing',
                    step: function() {
                        $('#track-cover').css({
                            "-webkit-filter": "blur("+this.blurRadius+"px)",
                            "filter": "blur("+this.blurRadius+"px)"
                        });
                    }
                });
                audioElement.setAttribute('src', track.download_url);
                audioElement.restart();
                setTimeout(() => { console.log("animated"); }, 2000);
                $("#track-cover").css({
                    "-webkit-filter": "blur(0px);",
                    "filter": "blur(0px);"
                });
                $("#score-username").html("6");
                break;

            default:
                console.log("PLZ TO HELP");
                console.log(gameState);
                break;
        }

        document.players = gameInfo.players;
    };

    document.ws = socket; /* debugging */
    if (socket.readyState === WebSocket.OPEN) {
      socket.onopen();
    }
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

/*class Player {
    constructor() {
        this.username = "";
        this.points = 0;
        this.correct = false;
        this.picture = "";
    }
}*/