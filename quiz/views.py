from django.shortcuts import render
from users.forms import CustomUserCreationForm, CustomAuthenticationForm
from .deezer import get_random_track


def index(request):
    rform = CustomUserCreationForm().as_p()
    aform = CustomAuthenticationForm().as_p()
    track = None
    #if request.user.is_authenticated:
    #    track, song = get_random_track()
    #    request.user.song_history.add(song)
    context = {
        'track': track,
        'rform': rform,
        'aform': aform,
    }
    return render(request, 'index.html', context)
