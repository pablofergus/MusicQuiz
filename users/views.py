from django.contrib import messages
from django.contrib.auth import logout as django_logout, authenticate
from django.contrib.auth import login as django_login
from django.http import HttpResponse
from django.shortcuts import render, redirect

from .forms import CustomUserCreationForm, CustomAuthenticationForm, ValidationError


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password1')
            user.set_password(password)
            user.save()
            django_login(request, user)
            messages.success(request, 'Account created for {username}')

        return redirect('index')
    return redirect('index')


def login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user_cache = authenticate(username=username, password=password)
            if user_cache is None:
                raise ValidationError("Username or password incorrect")
            print("hi " + str(user_cache))
            django_login(request, user_cache)
            return redirect('index')
    return HttpResponse('wrong... please to help')


def logout(request):
    django_logout(request)
    return redirect('index')
