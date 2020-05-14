from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render

from quiz.forms import CustomGameCreationForm, SettingsForm
from quiz.models import Game
from users.forms import CustomAuthenticationForm, CustomUserCreationForm


def index(request):
    games = [g.toJSON() for g in Game.objects.all()]
    rform = CustomUserCreationForm(auto_id='register-%s').as_p()
    aform = CustomAuthenticationForm(auto_id='login-%s').as_p()
    gform = CustomGameCreationForm(auto_id='game-creation-%s').as_p()
    sform = SettingsForm(auto_id='game-settings-%s').as_p()
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
    rform = CustomUserCreationForm(auto_id='register-%s').as_p()
    aform = CustomAuthenticationForm(auto_id='login-%s').as_p()
    gform = CustomGameCreationForm(auto_id='game-creation-%s').as_p()
    sform = SettingsForm(auto_id='game-settings-%s').as_p()
    game = Game.objects.get(pk=game_id)
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
