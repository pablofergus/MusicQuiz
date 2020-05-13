from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('lobby/<int:game_id>/', views.lobby, name='lobby'),
    path('new-room/', views.new_room, name="new_room"),
]
