from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render

from quiz.forms import CustomGameCreationForm, SettingsForm
from quiz.models import Game, GameInfo
from users.forms import CustomAuthenticationForm, CustomUserCreationForm


def index(request):
    games = [g.toJSON() for g in Game.objects.all()]
    rform = CustomUserCreationForm().as_p()
    aform = CustomAuthenticationForm().as_p()
    gform = CustomGameCreationForm().as_p()
    sform = SettingsForm().as_p()
    # if request.user.is_authenticated:
    #    track, song = get_random_track()
    #    request.user.song_history.add(song)
    context = {
        'gform': gform,
        'games': games,
        'rform': rform,
        'aform': aform,
        'sform': sform,
    }
    return render(request, 'index.html', context)


def lobby(request, game_id):
    rform = CustomUserCreationForm().as_p()
    aform = CustomAuthenticationForm().as_p()
    gform = CustomGameCreationForm().as_p()
    game = Game.objects.get(pk=game_id)
    sform = SettingsForm().as_p()
    context = {
        'game': game,
        'gform': gform,
        'rform': rform,
        'aform': aform,
        'sform': sform,
    }
    return render(request, 'index.html', context)


def new_room(request):
    if request.method == 'POST':
        form = CustomGameCreationForm(data=request.POST)
        if form.is_valid():
            game = form.save(commit=False)
            name = form.cleaned_data.get('name')
            password = form.cleaned_data.get('password')
            game.set_password(password)
            game.save()
            print("Creating a game: " + name)
            return HttpResponseRedirect("/lobby/" + str(game.id))

    return HttpResponse('wrong... please to help')
