GAME_STATES = {
    "WAITING_IN_LOBBY": "Waiting in lobby",
    "READY": "Ready",
    "LOADING": "Loading",
    "GUESSING": "Guessing",
    "POST_ANSWERS": "Post answers",
    "RESULTS": "Results",
    "VICTORY": "Victory",
}

$(document).ready(function() {
    let audioElement = document.createElement('audio');
    audioElement.muted = true;
    let volume = 0.3;
    let slider = document.getElementById("volume-slider");
    let gameState = GAME_STATES.WAITING_IN_LOBBY;
    let pause = false;
    let players = [];

    const socket = new WebSocket(
            'ws://'
            + window.location.host
            + '/ws/quiz/'
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

    audioElement.addEventListener('ended', function() {
            this.play();
    }, false);

    audioElement.addEventListener("canplay",function(){
        $("#timer").text(audioElement.duration-1);
        //socket.send("canplay");
        this.volume = volume;
        audioElement.muted = false;
        audioElement.play();
    });

    audioElement.addEventListener("timeupdate",function(){
        $("#currentTime").text(Math.floor(30-audioElement.currentTime));
    });

    $('#pause').click(function() {
        if(!pause)
            audioElement.pause();
        else
            audioElement.play();
        pause = !pause;
        var infos = pause ? "pause" : "resume";
        console.log(infos);
        socket.send(infos);
    });

    $('#restart').click(function() {
        audioElement.currentTime = 0;
    });

    socket.onopen = function open() {
      console.log('WebSockets connection created.');
      //socket.send("I have connected")
    };

    socket.onmessage = function message(event) {
        var data = JSON.parse(event.data),
            gameInfo = JSON.parse(data),
            track = gameInfo.track;
        console.log(gameInfo); 
        gameState = gameInfo.game_state;

        var userhtml = "";
        for(var i = 0; i < gameInfo.num_players; i++) {
            userhtml += "<div class=\"col-lg-" + String(Math.floor(12/gameInfo.num_players)) + " col-md-6 mb-md-4\">" +
                    "<div class=\"box featured\" data-aos=\"zoom-in\">" +
                        "<h3>" + String(gameInfo.players[i].user.username) + "</h3>" +
                        "<h4>" + String(gameInfo.players[i].points) + "<span> point" + (gameInfo.players[i].points === 1 ? "" : "s") + "</span></h4>" +
                    "</div>" +
                "</div>";
            $("#user-scores").html(userhtml);
            console.log(gameInfo.players[0].points);
        }

        switch (gameState) {
            case GAME_STATES.GUESSING:
                $("#artist").html("¿¿¿¿¿¿");
                $("#title").html("??????");
                $("#track-cover").html("<img src=\"" + track.album.cover + "\"/>");
                audioElement.setAttribute('src', track.download_url);
                $('#track-cover').css({
                    "-webkit-filter": "blur(50px)",
                    "filter": "blur(50px)"
                });
                break;

            case GAME_STATES.POST_ANSWERS:            
                userAnswer = $("#useranswer").val();
                $("#useranswer").val("");
                socket.send(userAnswer);
                break;

            case GAME_STATES.RESULTS:
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
                setTimeout(() => { console.log("animated"); }, 2000);
                $("#track-cover").css({
                    "-webkit-filter": "blur(0px);",
                    "filter": "blur(0px);"
                });
                $("#score-username").html("6");
                break;

            default:
                console.log("PLZ TO HELP");
                console.log(gameState)
                break;
        }

        document.players = gameInfo.players;
    };

    document.ws = socket; /* debugging */
    if (socket.readyState === WebSocket.OPEN) {
      socket.onopen();
    }
});

$( window ).on("unload", function(e) {
    const socket = new WebSocket(
        'ws://'
        + window.location.host
        + '/ws/quiz/'
    );
    console.log("DISCONNECTED");
    socket.close();
});

/*class Player {
    constructor() {
        this.username = "";
        this.points = 0;
        this.correct = false;
        this.picture = "";
    }
}*/