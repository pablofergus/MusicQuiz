import asyncio

from channels.layers import get_channel_layer
from django.contrib.auth.hashers import make_password, check_password
from fuzzywuzzy import fuzz
from math import ceil

from quiz.deezer import get_genre_list, get_genre_radio, pop_genre_radio_track
from quiz.basemodels import *
from users.models import User


class Game(models.Model):
    radio = models.ManyToManyField('quiz.Song')
    info = models.OneToOneField('quiz.GameInfo', on_delete=models.CASCADE)
    running = models.BooleanField(default=False)

    def __str__(self):
        return str(self.info)

    def toJSON(self):
        return {
            "radio": [s for s in self.radio.all()],
            "info": self.info.toJSON(),
            "running": self.running,
            "id": self.id,
        }

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self._password = raw_password

    def check_password(self, raw_password):
        """
        Return a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """
        def setter(raw_password):
            self.set_password(raw_password)
            # Password hash upgrades shouldn't be considered password changes.
            self._password = None
            self.save(update_fields=["password"])
        return check_password(raw_password, self.password, setter)

    async def run(self):
        if not Game.objects.get(pk=self.id).running:
            loop = asyncio.get_event_loop()
            loop.create_task(self.long_running())

    async def run_after_posted(self):
        if self.info.game_state == GameStates.POST_ANSWERS and not Game.objects.get(pk=self.id).running:
            loop = asyncio.get_event_loop()
            loop.create_task(self.long_running())
            print("Continuing game...")

    async def long_running(self):
        automaton = {
            GameStates.WAITING_IN_LOBBY: self.waiting_in_lobby,
            GameStates.READY: self.ready,
            GameStates.LOADING: self.loading,
            GameStates.GUESSING: self.guessing,
            GameStates.POST_ANSWERS: self.post_answers,
            GameStates.RESULTS: self.results,
            GameStates.VICTORY: self.victory,
            GameStates.PAUSE: self.pause,
        }
        self.running = True
        self.save()
        try:
            while Game.objects.get(pk=self.id) and self.running is True and self.info.game_state is not None:
                print(self.info.game_state)
                self.info.save()
                state = automaton.get(self.info.game_state)
                await state()
        except Game.DoesNotExist:
            print("Does not exist")
            pass

    @staticmethod
    def stop():
        print("Destroying game :>")
        asyncio.Task.current_task().cancel()

    async def update_all_clients(self):
        self.info.save()
        for p in self.info.players.all():
            channel_layer = get_channel_layer()
            await channel_layer.send(
                p.channel_name,
                {
                    "type": "update.game.info",
                    "text": self.info.toJSON()
                }
            )

    async def add_user(self, channel_name, username):
        user = User.objects.filter(username=username).first()

        player, created = Player.objects.get_or_create(user=user)
        self.info = Game.objects.get(pk=self.id).info
        if not created:
            setattr(player, "channel_name", channel_name)
            setattr(player, "game_id", self.id)
            player.save()
            self.info.players.add(player)
        else:
            setattr(player, "game_id", self.id)
            setattr(player, "channel_name", channel_name)
            player.save()
            print("CREATED PLAYER " + player.user.username)
            self.info.players.add(player)
        self.info.num_players = self.info.players.count()
        print(player.user.username + " has joined the game, number " + str(self.info.num_players))
        return await self.update_all_clients()
        #if len(self.game_info.players) is 1:
            #await self.run()

    async def remove_user(self, channel_name):
        self.info = Game.objects.get(pk=self.id).info
        player, _ = Player.objects.get_or_create(channel_name=channel_name)
        print(player.user.username + " has left the game")
        self.info.players.remove(player)
        player.delete()
        self.info.num_players = self.info.players.count()
        if self.info.num_players is 0:
            GameInfo.objects.get(pk=self.info.id).delete()
            #Game.objects.get(pk=self.id).delete()
            Game.stop()
        else:
            await self.update_all_clients()

    def add_to_song_history(self):
        for p in self.info.players.all():
            if p.user.username is not 'AnonymousUser':
                p.user.song_history.add(Song.objects.filter(download_url=self.info.track.download_url).first())

    async def waiting_in_lobby(self):
        self.info = Game.objects.get(pk=self.id).info
        await self.update_all_clients()
        all_ready = True
        for p in self.info.players.all():
            if not p.ready:
                all_ready = False
                break
        if all_ready:
            self.info.game_state = GameStates.READY
        else:
            self.running = False
            self.save()
            self.stop()

    async def ready(self):
        print("Starting game...")
        self.info = Game.objects.get(pk=self.id).info
        await self.update_all_clients()
        self.info.game_state = GameStates.LOADING

    async def loading(self):
        self.info = Game.objects.get(pk=self.id).info
        await self.update_all_clients()
        genres = get_genre_list()
        if self.radio.count() is 0:
            print("loading radio...")
            radio_deezer = get_genre_radio(genres[5])
            while len(radio_deezer) > 1:
                _, song, radio_deezer = pop_genre_radio_track(radio_deezer)
                self.radio.add(song)
        self.info.game_state = GameStates.GUESSING

    async def guessing(self):
        self.info = Game.objects.get(pk=self.id).info
        #TODO: self.track, song = get_random_track() etc...
        self.info.track = self.radio.all().first()
        #print("RADIO SONG: " + self.radio.all().first())
        self.info.track.save()
        self.radio.remove(self.radio.all().first())
        self.add_to_song_history()
        await self.update_all_clients()
        self.info.num_answers = 0
        self.info.save()
        self.info.game_state = GameStates.POST_ANSWERS
        await asyncio.sleep(30)

    async def post_answers(self):
        self.info = Game.objects.get(pk=self.id).info
        if self.info.num_answers is 0:
            await self.update_all_clients()
            print("STOPPING GAME")
            self.running = False
            self.save()
            self.info.save()
            await asyncio.sleep(2)
            if not getattr(Game.objects.get(pk=self.id), 'running'):
                print("TIMED OUT" + str(getattr(Game.objects.get(pk=self.id), 'running')))
                self.info.num_answers = -1
                self.info.save()
                await self.run_after_posted()
                self.stop()
            return
        else:
            self.info.num_answers = 0
            self.info.game_state = GameStates.RESULTS

    async def results(self):
        self.info = Game.objects.get(pk=self.id).info
        for p in self.info.players.all():
            r1 = fuzz.partial_ratio(self.info.track.title.lower(), p.answer.lower())
            r2 = fuzz.partial_ratio(self.info.track.album.title.lower(), p.answer.lower())
            r3 = 0
            for a in self.info.track.artists.all():
                r3 += fuzz.partial_ratio(a.name.lower(), p.answer.lower()) #TODO: quizas bonus si averiguas artistas extra??
            points = ceil((r1 + r2 + r3)/10)
            print(points)
            p.points += points
            p.answer = ""
            p.save()

        await self.update_all_clients()
        self.info.game_state = GameStates.GUESSING
        await asyncio.sleep(30)

    async def victory(self):
        await asyncio.sleep(30)
        self.info.game_state = GameStates.WAITING_IN_LOBBY
        self.info.save()
        return self.info.game_state

    async def pause(self):
        return self.info.game_state
