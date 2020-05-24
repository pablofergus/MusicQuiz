from django.contrib.auth import authenticate
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
User = get_user_model()
 
 
class CustomUserCreationForm(forms.Form):
    username = forms.CharField(label='Username', min_length=4, max_length=20)
    email = forms.EmailField(label='Email')
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)
 
    def clean_username(self):
        username = self.cleaned_data['username']#.lower()
        r = User.objects.filter(username=username)
        if r.count():
            raise ValidationError("Username already exists")
        return username
 
    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        r = User.objects.filter(email=email)
        if r.count():
            raise ValidationError("Email already exists")
        return email
 
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
 
        if password1 and password2 and password1 != password2:
            raise ValidationError("Password don't match")
 
        return password2
 
    def save(self, commit=True):
        user = User.objects.create_user(
            self.cleaned_data['username'],
            self.cleaned_data['email'],
            self.cleaned_data['password1']
        )
        return user


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
        return password
