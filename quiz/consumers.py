import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer, WebsocketConsumer

from users.models import User
from .models import Game, GameTypes, Genre
from quiz.gamestates import GameStates


class UserMessages:
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    READY = "READY"
    UNREADY = "UNREADY"
    ANSWER = "ANSWER:"
    JOIN = "JOIN"
    REQUESTSETTINGS = "REQUEST SETTINGS"
    SETTINGS = "SETTINGS:"


class QuizConsumer(AsyncJsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game_state = GameStates.WAITING_IN_LOBBY

    async def connect(self):
        if str(self.scope['user']) is not 'AnonymousUser':
            await self.accept()
            print(self.scope["url_route"]["kwargs"]["stream"])
            try:
                game = Game.objects.get(pk=self.scope["url_route"]["kwargs"]["stream"])
                if game:
                    #if game.info.settings.private: TODO introduce password check if private game
                    #    authorized = game.check_password()
                    await game.add_player(self.channel_name, self.scope['user'].username)
                    if not game.running:
                        await game.run()
                    print("CONNECTION: " + str(self.scope['user']) + " to game " + str(game))
            except Game.DoesNotExist:
                pass

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        print("RECIEVED: " + text_data)
        if text_data == UserMessages.PAUSE:  # TODO
            self.game_state = GameStates.PAUSE

        if text_data == UserMessages.RESUME:
            self.game_state = GameStates.GUESSING

        if text_data == UserMessages.REQUESTSETTINGS:
            game = Game.objects.get(pk=self.scope["url_route"]["kwargs"]["stream"])
            await self.send(json.dumps(game.info.settings.toJSON()))

        if text_data.startswith(UserMessages.SETTINGS):
            game = Game.objects.get(pk=self.scope["url_route"]["kwargs"]["stream"])
            settings = game.info.settings
            new_settings = json.loads(text_data[len(UserMessages.SETTINGS):])
            settings.rounds = new_settings['rounds']
            settings.words = new_settings['words']
            settings.private = new_settings['private']
            settings.game_type = GameTypes.objects.filter(name=new_settings['game_type']).first()
            settings.genre = Genre.objects.filter(name=new_settings['genre']).first()
            game.set_password(new_settings['password'])
            settings.save()
            print("saved")

        if text_data == UserMessages.READY or text_data == UserMessages.UNREADY:
            p = Game.objects.get(pk=self.scope["url_route"]["kwargs"]["stream"]).info.players.filter(
                user=User.objects.filter(username=self.scope["user"].username).first()
            ).first()
            if text_data == UserMessages.READY:
                print(self.scope["user"].username + " is ready.")
                p.ready = True
                p.answer = "Ready"
            else:
                print(self.scope["user"].username + " is unready.")
                p.ready = False
                p.answer = "Not ready"
            p.save()
            game = Game.objects.get(pk=self.scope["url_route"]["kwargs"]["stream"])
            await game.run()

        if text_data == UserMessages.JOIN:
            game = Game.objects.get(pk=self.scope["url_route"]["kwargs"]["stream"])
            p = Game.objects.get(pk=self.scope["url_route"]["kwargs"]["stream"]).info.players.filter(
                user=User.objects.filter(username=self.scope["user"].username).first()
            ).first()
            p.ready = True
            p.save()
            await game.update_all_clients(state_change=False, join=True)

        if text_data.startswith(UserMessages.ANSWER):
            p = Game.objects.get(pk=self.scope["url_route"]["kwargs"]["stream"]).info.players.filter(
                user=User.objects.filter(username=self.scope["user"].username).first()
            ).first()
            if p:
                game = Game.objects.get(pk=self.scope["url_route"]["kwargs"]["stream"])
                setattr(p, "answer", text_data[len(UserMessages.ANSWER):])
                print(text_data[len(UserMessages.ANSWER):])
                p.save(update_fields=['answer'])
                game.info.num_answers += 1
                game.info.save(update_fields=['num_answers'])
                if game.info.num_answers == game.info.players.count():
                    print("gottem all")
                    return await game.run()

    async def disconnect(self, code):
        """
        When user disconnects from the game, he is removed and deleted.
        """
        print("DISCONNECTING..." + self.scope['user'].username)
        game = Game.objects.get(pk=self.scope["url_route"]["kwargs"]["stream"])
        if game:
            await game.remove_player(self.channel_name)

    async def update_game_info(self, event):
        """
        Called to update the clients when the game state changes.
        """
        game_info = event["text"]
        if game_info["game_state"] != GameStates.RESULTS:
            if game_info["track"] is not None:
                print(game_info["track"])
                game_info["track"]["title"] = ""
                game_info["track"]["album"]["title"] = ""
                i = 0
                for _ in game_info["track"]["artists"]:
                    game_info["track"]["artists"][i]["name"] = ""
                    i += 1
        await self.send_json(json.dumps(game_info))


class AdminQuizConsumer(WebsocketConsumer):
    pass
