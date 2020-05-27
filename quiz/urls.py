from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('lobby/<int:game_id>/', views.lobby, name='lobby'),
    re_path(r'^.*new-room/$', views.new_room, name="new_room"),
]
