import asyncio

from channels.layers import get_channel_layer
from django.contrib.auth.hashers import make_password, check_password
from fuzzywuzzy import fuzz
from math import ceil

from quiz.deezer import get_genre_list, get_enough_tracks
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
        """
        Hashes and sets password for the game
        """
        self.info.settings.password = make_password(raw_password)
        self.info.settings._password = raw_password

    def check_password(self, raw_password):
        """
        Return a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """

        def setter(raw_password):
            self.info.settings.set_password(raw_password)
            # Password hash upgrades shouldn't be considered password changes.
            self.info.settings._password = None
            self.info.settings.save(update_fields=["password"])

        return check_password(raw_password, self.info.settings.password, setter)

    async def run(self):
        """
        Creates the game task and starts the automaton.
        """
        if not Game.objects.get(pk=self.id).running:
            loop = asyncio.get_event_loop()
            loop.create_task(self.long_running())

    # async def run_after_posted(self):
    #    if self.info.game_state == GameStates.POST_ANSWERS and not Game.objects.get(pk=self.id).running:
    #        loop = asyncio.get_event_loop()
    #        loop.create_task(self.long_running())
    #        print("Continuing game...")

    async def long_running(self):
        """
        State machine function, loops through the states of the automaton.
        """
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
        print("Stopping thread...")
        asyncio.Task.current_task().cancel()

    async def update_all_clients(self, state_change=True, join=False):
        """
        Parses game info and sends it to each players channel.
        """
        self.info.num_players = self.info.players.count()
        self.info.save()
        channel_layer = get_channel_layer()
        info = self.info.toJSON()
        info["state_change"] = state_change
        for p in self.info.players.all():
            print(p.ready)
            if self.info.game_state == GameStates.WAITING_IN_LOBBY or p.ready or join:
                await channel_layer.send(
                    p.channel_name,
                    {
                        "type": "update.game.info",
                        "text": info,
                    }
                )

    async def add_player(self, channel_name, username):
        """
        Adds the user to the game, creating a player or re-adding him.
        """
        a = ""
        if self.info.game_state == GameStates.WAITING_IN_LOBBY:
            a = "Not ready"
        user = User.objects.filter(username=username).first()
        player, created = Player.objects.get_or_create(user=user, answer=a) #clean old players
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
        return await self.update_all_clients(state_change=False, join=True)

    async def remove_player(self, channel_name):
        """
        Removes the player from the game, and deletes him if TODO.
        Deletes the game if he was the last player left.
        """
        self.info = Game.objects.get(pk=self.id).info
        player, _ = Player.objects.get_or_create(channel_name=channel_name)
        print(player.user.username + " has left the game")
        self.info.players.remove(player)
        player.delete()
        self.info.num_players = self.info.players.count()
        if self.info.num_players is 0:
            GameInfo.objects.get(pk=self.info.id).delete()
            print("Destroying the game :>")
            Game.stop()
        else:
            await self.update_all_clients(state_change=False)

    def add_to_song_history(self):
        """
        Saves current track to each players history.
        """
        for p in self.info.players.all():
            if p.user.username is not 'AnonymousUser':
                p.user.song_history.add(Song.objects.filter(download_url=self.info.track.download_url).first())

    async def update_genre_list(
            self):  # TODO genres have names and ids, and manytomany radios. Make new model of radios.
        genres = await get_genre_list()
        self.info = Game.objects.get(pk=self.id).info
        Genre.objects.all().delete()
        for genre in genres:
            Genre.objects.create(
                name=genre['title'],
                deezer_id=genre['id'],
                picture=genre['picture_medium'],
                tracklist=genre['tracklist'],
            )

    async def waiting_in_lobby(self):
        """
        Checks if all players are ready. If ready, passes to READY.
        """
        # await self.update_genre_list()
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
        for p in self.info.players.all():  # After update clear answers
            p.answer = ""
            p.save()
        self.info = Game.objects.get(pk=self.id).info
        await self.update_all_clients()
        self.info.game_state = GameStates.LOADING

    async def loading(self):
        """
        Obtains the necessary deezer info for the game.
        """
        self.info = Game.objects.get(pk=self.id).info
        await self.update_all_clients()
        if self.info.settings.game_type.type_id is 3:
            print("loading random tracks...")
            songs = await get_enough_tracks(self.info.settings.rounds, random=True)
            self.radio.add(*songs)

        if self.info.settings.game_type.type_id is 2:
            print("loading charts...")
            songs = await get_enough_tracks(self.info.settings.rounds, charts=True)
            self.radio.add(*songs)

        if self.info.settings.game_type.type_id is 1:
            # genres = get_genre_list()
            print("loading radio " + self.info.settings.genre.name)
            songs = await get_enough_tracks(self.info.settings.rounds, genre=self.info.settings.genre.tracklist)
            self.radio.add(*songs)
        self.info.game_state = GameStates.GUESSING

    async def guessing(self):
        """
        Pops a track from the radio, and sets it as current track. After 30s passes to POST_ANSWERS.
        """
        self.info = Game.objects.get(pk=self.id).info

        if not self.radio.all().first():
            self.info.game_state = GameStates.VICTORY
            return

        self.info.track = self.radio.all().first()
        self.info.track.save()
        self.radio.remove(self.radio.all().first())
        self.add_to_song_history()

        self.info.round += 1
        await self.update_all_clients()
        self.info.num_answers = 0
        self.info.save()

        await asyncio.sleep(30)
        self.info.game_state = GameStates.POST_ANSWERS

    async def post_answers(self):
        """
        Sets a timeout for the answers to arrive. Checks if game is continuing with self.running.
        If run() has not been executed after the timeout, it passes to RESULTS.
        If it has, the thread is killed.
        """
        self.info = Game.objects.get(pk=self.id).info
        if self.info.num_answers is 0:
            await self.update_all_clients()
            print("STOPPING GAME")
            self.running = False
            self.save()
            await asyncio.sleep(2)

            if not getattr(Game.objects.get(pk=self.id), 'running'):
                print("TIMED OUT (running is " + str(getattr(Game.objects.get(pk=self.id), 'running')) + ")")
                self.info.game_state = GameStates.RESULTS
                self.running = True
                self.save()
                self.info.save()
            else:
                self.stop()
        else:
            self.info.game_state = GameStates.RESULTS

    async def results(self):
        """
        Calculates a score for each player and waits for another play of the song.
        """
        self.info = Game.objects.get(pk=self.id).info
        for p in self.info.players.all():
            r1 = fuzz.partial_ratio(self.info.track.title.lower(), p.answer.lower())
            r2 = fuzz.partial_ratio(self.info.track.album.title.lower(), p.answer.lower())
            r3 = 0
            for a in self.info.track.artists.all():
                r3 += fuzz.partial_ratio(a.name.lower(),
                                         p.answer.lower())  # TODO: quizas bonus si averiguas artistas extra??
            points = ceil((r1 + r2 + r3) / 10)
            print(points)
            p.points += points
            p.user.total_points += points
            p.user.save()
            p.save()

        await self.update_all_clients()
        for p in self.info.players.all():  # After update clear answers
            p.answer = ""
            p.save()
        await asyncio.sleep(30)
        self.info.game_state = GameStates.GUESSING

    async def victory(self):
        await asyncio.sleep(30)
        self.info.game_state = GameStates.WAITING_IN_LOBBY
        self.info.save()
        return self.info.game_state

    async def pause(self):
        return self.info.game_state
