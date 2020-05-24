from __future__ import absolute_import, unicode_literals

import json

from celery import shared_task

from quiz.basemodels import Song, Album, Artist


@shared_task
def save_song(track):
    #track = json.loads(track)
    print(track)
    song = Song.objects.filter(download_url=track['download_url'])
    if not Song.objects.filter(download_url=track['download_url']).exists():
        album, _ = Album.objects.get_or_create(
            title=track['album'],
            cover=track['cover'],
        )
        song = Song.objects.create(
            title=track['title'],
            download_url=track['download_url'],
            album=album
        )
        print(song)
        for a in track['contributors']:
            artist, _ = Artist.objects.get_or_create(
                name=a['name'],
                picture=a['picture'],
                fans=a['fans'],
                albums=a['albums']
            )
            song.artists.add(artist)
    else:
        song = song.first()
    return song.id
