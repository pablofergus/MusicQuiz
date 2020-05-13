from django import forms
from django.core.exceptions import ValidationError

from quiz.basemodels import GameInfo
from quiz.models import Game


class CustomGameCreationForm(forms.Form):
    name = forms.CharField(label='Name', min_length=4, max_length=20)
    private = forms.BooleanField(label="Private")
    password = forms.CharField(label='Password (if private)', widget=forms.PasswordInput)

    def clean_username(self):
        name = self.cleaned_data['name'].lower()
        """r = GameInfo.objects.filter(name=name)
        if r.count():
            raise ValidationError("Username already exists")"""
        return name

    def clean_password(self):
        return self.cleaned_data.get('password')

    def save(self, commit=True):
        info = GameInfo.objects.create(name=self.cleaned_data['name'])
        game = Game.objects.create(
            info=info,
            private=self.cleaned_data['private'],
            password=self.cleaned_data['password']
        )
        return game

"""
class CustomAuthenticationForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'autofocus': True}),
        max_length=50,
        required=True,
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput,
        required=True,
    )

    def __init__(self, request=None, *args, **kwargs):
        self.user_cache = None
        self.request = request
        super(CustomAuthenticationForm, self).__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username'].lower()
        r = User.objects.filter(username=username)
        if not r.count():
            raise ValidationError("Username does not exist")
        return username

    def clean_password(self):
        password = self.cleaned_data['password']
        username = self.data.get('username').lower()
        return password"""
