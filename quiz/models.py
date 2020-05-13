import asyncio

from channels.layers import get_channel_layer
from fuzzywuzzy import fuzz
from math import ceil

from quiz.deezer import get_genre_list, get_genre_radio, pop_genre_radio_track
from quiz.basemodels import *


class Game(models.Model):
    radio = models.ManyToManyField('quiz.Song')
    info = models.OneToOneField('quiz.GameInfo', on_delete=models.CASCADE)
    running = models.BooleanField(default=False)

    async def run(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self.long_running())
        print("Starting game...")

    async def run_after_posted(self):
        if self.info.game_state == GameStates.POST_ANSWERS and not self.running:
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
        print("SAVEDRUNNINGSTATE" + str(self.running))
        while self.running is True and self.info.game_state is not None:
            print(self.info.game_state)
            state = automaton.get(self.info.game_state)
            await state()

    async def update_all_clients(self):
        self.info.save()
        for p in self.info.players.all():
            #await p.conn.update_game_info(self.info) #TODO
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
        self.info = Game.objects.first().info
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

    async def remove_user(self, channel_name): #TODO
        self.info = Game.objects.first().info
        player = Player.objects.get_or_create(channel_name=channel_name)
        print(player.user.username + " has left the game")
        self.info.players.remove(player)
        player.delete()
        await self.update_all_clients()

    def add_to_song_history(self):
        for p in self.info.players.all():
            if p.user.username is not 'AnonymousUser':
                p.user.song_history.add(Song.objects.filter(download_url=self.info.track.download_url).first())

    async def waiting_in_lobby(self):
        self.info = Game.objects.first().info
        await self.update_all_clients()
        self.info.game_state = GameStates.READY
        self.info.save()

    async def ready(self):
        self.info = Game.objects.first().info
        await self.update_all_clients()
        self.info.game_state = GameStates.LOADING
        self.info.save()

    async def loading(self):
        self.info = Game.objects.first().info
        await self.update_all_clients()
        genres = get_genre_list()
        if self.radio.count() is 0:
            print("loading radio...")
            radio_deezer = get_genre_radio(genres[5])
            while len(radio_deezer) > 1:
                _, song, radio_deezer = pop_genre_radio_track(radio_deezer)
                self.radio.add(song)
        self.info.game_state = GameStates.GUESSING
        self.info.save()

    async def guessing(self):
        self.info = Game.objects.first().info
        #TODO: self.track, song = get_random_track() etc...
        self.info.track = self.radio.all().first()
        #print("RADIO SONG: " + self.radio.all().first())
        self.info.track.save()
        self.radio.remove(self.radio.all().first())
        self.add_to_song_history()
        await self.update_all_clients()
        await asyncio.sleep(30)
        self.info.num_answers = 0
        self.info.save()
        self.info.game_state = GameStates.POST_ANSWERS
        self.info.save()

    async def post_answers(self):
        self.info = Game.objects.first().info
        if self.info.num_answers is 0:
            await self.update_all_clients()
            print("STOPPING GAME")
            self.running = False
            self.save()
            self.info.save()
            await asyncio.sleep(2)
            if not getattr(Game.objects.first(), 'running'): #TODO
                print("TIMED OUT" + str(getattr(Game.objects.first(), 'running')))
                self.info.num_answers = -1
                self.info.save()
                return await self.run_after_posted()
            return
        else:
            self.info.num_answers = 0
            self.info.save()
            self.info.game_state = GameStates.RESULTS
            self.info.save()

    async def results(self):
        self.info = Game.objects.first().info
        i = 0
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
            i += 1

        await self.update_all_clients()
        await asyncio.sleep(30)
        self.info.game_state = GameStates.GUESSING
        self.info.save()

    async def victory(self):
        await asyncio.sleep(30)
        self.info.game_state = GameStates.WAITING_IN_LOBBY
        self.info.save()
        return self.info.game_state

    async def pause(self):
        return self.info.game_state
