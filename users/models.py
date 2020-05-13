from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse


class User(AbstractUser):
    spotify_id = models.CharField(max_length=50, default="")
    total_points = models.BigIntegerField(default=0)
    level = models.IntegerField(default=0)
    song_history = models.ManyToManyField('quiz.Song')
    picture = models.URLField(null=True)

    def get_absolute_url(self):
        """Returns the url to access a particular instance of the model."""
        return reverse('model-detail-view', args=[str(self.id)])

    def toJSON(self):
        return {
            "spotify_id": self.spotify_id,
            "total_points": self.total_points,
            "level": self.level,
            "username": self.username,
            "email": self.email,
            "picture": self.picture,
        }
