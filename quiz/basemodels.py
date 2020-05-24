from django.db import models
from django.urls import reverse
from django.utils.deconstruct import deconstructible

from quiz.gamestates import GameStates


class Genre(models.Model):
    name = models.CharField(max_length=128)
    deezer_id = models.IntegerField()
    tracklist = models.URLField(null=True, blank=True)
    picture = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name


class Artist(models.Model):
    name = models.CharField(max_length=300)
    picture = models.URLField()
    fans = models.IntegerField(null=True, blank=True)
    albums = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

    def toJSON(self):
        return {"name": self.name, "picture": self.picture, "fans": self.fans, "albums": self.albums}

    def get_absolute_url(self):
        """Returns the url to access a particular instance of the model."""
        return reverse('model-detail-view', args=[str(self.id)])


class Album(models.Model):
    title = models.CharField(max_length=300)
    cover = models.URLField()

    def __str__(self):
        return self.title

    def toJSON(self):
        return {"title": self.title, "cover": self.cover}


class Song(models.Model):
    artists = models.ManyToManyField(Artist)
    title = models.CharField(max_length=300)
    download_url = models.URLField()
    saved_by = models.ManyToManyField('users.User')
    album = models.ForeignKey('quiz.Album', on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def toJSON(self):
        result = {
            "id": self.id,
            "title": self.title,
            "download_url": self.download_url,
            "album": {"title": self.album.title, "cover": self.album.cover,},
            "artists": [],
        }
        for a in self.artists.all():
            result["artists"].append(a.toJSON())
        return result

    def get_absolute_url(self):
        """Returns the url to access a particular instance of the model."""
        return reverse('model-detail-view', args=[str(self.id)])


class Player(models.Model):
    channel_name = models.CharField(max_length=50)
    user = models.ForeignKey('users.User', on_delete=models.DO_NOTHING)
    points = models.IntegerField(default=0)
    correct = models.IntegerField(default=0)
    answer = models.CharField(max_length=150, default="")
    game_id = models.IntegerField(null=True, blank=True)
    ready = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def toJSON(self):
        return {
            "channel_name": self.channel_name,
            "points": self.points,
            "correct": self.correct,
            "answer": self.answer,
            "game_id": self.game_id,
            "user": self.user.toJSON()
        }


#@deconstructible
class GameTypes(models.Model):
    type_id = models.IntegerField()
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class GameSettings(models.Model):
    rounds = models.IntegerField(default=15)
    private = models.BooleanField(default=False)
    password = models.CharField(max_length=128)
    game_type = models.ForeignKey(
        'quiz.GameTypes',
        on_delete=models.CASCADE,
        #default=GameTypes.objects.first(),
        null=True,
        blank=True,
    )
    genre = models.ForeignKey(
        'quiz.Genre',
        on_delete=models.CASCADE,
        #default=GameTypes.objects.first(),
        null=True,
        blank=True,
    )
    words = models.TextField(blank=True)

    def toJSON(self):
        return {
            'rounds': self.rounds,
            'private': self.private,
            'game_type': str(self.game_type),
            'genre': str(self.genre),
            'words': self.words,
        }


class GameInfo(models.Model):
    track = models.ForeignKey('quiz.Song', null=True, blank=True, on_delete=models.PROTECT)
    players = models.ManyToManyField(Player)
    num_players = models.IntegerField(default=0)
    game_state = models.CharField(max_length=20, default=GameStates.WAITING_IN_LOBBY)
    num_answers = models.IntegerField(default=0)
    name = models.CharField(max_length=50)
    settings = models.OneToOneField('quiz.GameSettings', on_delete=models.CASCADE)
    round = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def toJSON(self):
        result = {
            "num_players": self.num_players,
            "game_state": self.game_state,
            "num_answers": self.num_answers,
            "name": self.name,
            "players": [],
            "round": self.round,
            "total_rounds": self.settings.rounds,
        }
        if self.track:
            result["track"] = self.track.toJSON()
        else:
            result["track"] = None
        for p in self.players.all():
            result["players"].append(p.toJSON())
        return result

