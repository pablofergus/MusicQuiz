from django import forms
from django.core.validators import EMPTY_VALUES

from quiz.models import Game, GameInfo, GameSettings, GameTypes, Genre


class CustomGameCreationForm(forms.Form):
    name = forms.CharField(label='Name', min_length=4, max_length=20,
                           widget=forms.TextInput(attrs={'autocomplete': 'nope'}))
    private = forms.BooleanField(label="Private", required=False)
    password = forms.CharField(
        label='Password (if private)',
        widget=forms.PasswordInput(attrs={'autocomplete': 'nope'}),
        required=False)

    def clean(self):
        private = self.cleaned_data.get('private', False)
        if private:
            password = self.cleaned_data.get('password', None)
            if password in EMPTY_VALUES:
                self._errors['password'] = self.error_class(['Password required if private'])
        return self.cleaned_data

    def clean_username(self):
        name = self.cleaned_data['name'].lower()
        """r = GameInfo.objects.filter(name=name)
        if r.count():
            raise ValidationError("Username already exists")"""
        return name

    def save(self, commit=True):
        settings = GameSettings.objects.create(
            private=self.cleaned_data['private'],
            password=self.cleaned_data['password']
        )
        info = GameInfo.objects.create(name=self.cleaned_data['name'], settings=settings)
        game = Game.objects.create(info=info)
        return game


TITLE_CHOICES = [
    ('MR', 'Mr.'),
    ('MRS', 'Mrs.'),
    ('MS', 'Ms.'),
]


class SettingsForm(forms.Form):
    rounds = forms.IntegerField(label="Rounds", min_value=1, max_value=50, widget=forms.NumberInput(attrs={'type':'range', 'step': '1'}))
    private = forms.BooleanField(label="Private", required=False, widget=forms.CheckboxInput())
    password = forms.CharField(
        label='Password (if private)',
        widget=forms.PasswordInput(attrs={'autocomplete': 'nope'}),
        required=False)
    game_type = forms.ModelChoiceField(label="Game type", queryset=GameTypes.objects.all())
    genre = forms.ModelChoiceField(label="Game type", queryset=Genre.objects.all())
    words = forms.CharField(label="Search terms (separated with ,)", widget=forms.Textarea(), required=False)
