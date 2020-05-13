import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer, WebsocketConsumer

from quiz.basemodels import GameInfo
from users.models import User
from .models import Game
from quiz.gamestates import GameStates


class QuizConsumer(AsyncJsonWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game_state = GameStates.WAITING_IN_LOBBY

    async def connect(self):
        #self.channel_name
        if str(self.scope['user']) is not 'AnonymousUser':
            await self.accept()
            if not Game.objects.first():
                print("Creating game...")
                info = GameInfo.objects.create(name="gibberish")
                game = Game.objects.create(info=info)
                await game.run()
            #if not Game.objects.first().running:
                #Game.objects.first().info.game_state = GameStates.WAITING_IN_LOBBY
                #Game.objects.first().run()
            await Game.objects.first().add_user(self.channel_name, self.scope['user'].username)
            print("CONNECTION: " + str(self.scope['user']))

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        print("RECIEVED: " + text_data)
        if text_data is "pause":
            self.game_state = GameStates.PAUSE
        if text_data is "resume":
            self.game_state = GameStates.GUESSING
        else:
            p = Game.objects.first().info.players.filter(
                user=User.objects.filter(username=self.scope["user"].username).first()
            ).first()
            if p:
                game = Game.objects.first() #TODO
                setattr(p, "answer", text_data)
                p.save(update_fields=['answer'])
                game.info.num_answers += 1
                game.info.save(update_fields=['num_answers'])
                if game.info.num_answers == game.info.players.count():
                    print("gottem all")
                    return await game.run_after_posted()
            #TODO save, and process signal

    async def disconnect(self, code):
        print("DISCONNECTING..." + self.scope['user'].username)
        #await self.game.remove_user(self)
        pass

    async def update_game_info(self, event):
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
