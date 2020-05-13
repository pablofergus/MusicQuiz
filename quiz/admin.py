from django.contrib import admin

from quiz.models import Game, Player, GameInfo, Album
from .basemodels import Song, Artist
from users.models import User

# Register your models here.
admin.site.register(User)
admin.site.register(Song)
admin.site.register(Artist)
admin.site.register(Game)
admin.site.register(GameInfo)
admin.site.register(Player)
admin.site.register(Album)