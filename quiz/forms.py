from django import forms
from django.core.validators import EMPTY_VALUES

from quiz.models import Game, GameInfo, GameSettings


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
