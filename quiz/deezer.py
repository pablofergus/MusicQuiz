import json
import requests
import random

from quiz.basemodels import Song, Artist, Album
from .exceptions import DeezerApiResponseException


# https://api.deezer.com/track/3135556
# https://api.deezer.com/search?q=bpm_min:120 dur_min:300


def get_random_track(filters=None):
    search = []
    while not search:
        word = get_random_word()
        search = get_search(word)
    print(word)
    track = DeezerTrack(search[0])
    song = save_song(track)
    return track, song


def get_chart_track(filters=None):
    charts = get_charts()
    track = select_track(charts)
    save_song(track)
    return track


def pop_genre_radio_track(tracklist, filters=None):
    url = "https://api.deezer.com/track/" + str(tracklist[0]['id'])
    track = DeezerTrack(request_and_parse(url))
    del tracklist[0]
    song = save_song(track)
    return track, song, tracklist


def select_track(tracks, filters=None):
    url = "https://api.deezer.com/track?q=?order=RANKING"
    return random.choice(tracks)


def get_charts(filters=None):
    url = "https://api.deezer.com/editorial/0/charts"
    return request_and_parse(url)['tracks']['data']


def get_search(query, filters=None):
    url = "https://api.deezer.com/search/?q=" + str(query) + "&order=RATING_DESC"  # "&order=RANKING"
    return request_and_parse(url)['data']


def get_genre_radio(genre, filters=None):  # TODO
    print(genre)
    return request_and_parse(genre['tracklist'])['data']


def get_genre_list():
    url = "https://api.deezer.com/genre/0/radios"
    return request_and_parse(url)['data']


def get_random_word():
    url = "https://random-word-api.herokuapp.com/word?number=1"
    return request_and_parse(url)[0]


def request_and_parse(url):
    response = requests.get(url)
    if response.status_code is 200:
        return json.loads(response.text)
    else:
        raise DeezerApiResponseException


class DeezerTrack:

    def __init__(self, track):
        self.title = track['title']
        self.album = track['album']['title']
        self.cover = track['album']['cover_big']
        self.download_url = track['preview']

        response = requests.get("https://api.deezer.com/artist/" + str(track['artist']['id']))
        artist = json.loads(response.text)
        self.contributors = []
        self.contributors.append(DeezerArtist(
            artist['name'],
            artist['picture_medium'],
            artist['nb_fan'],
            artist['nb_album']))
        if 'contributors' in track:
            for a in track['contributors']:
                if a['name'] is not self.contributors[0].name:
                    response = requests.get("https://api.deezer.com/artist/" + str(a['id']))
                    artist = json.loads(response.text)
                    self.contributors.append(Artist(
                        artist['name'],
                        artist['picture_medium'],
                        artist['nb_fan'],
                        artist['nb_album']))

    def toJSON(self):
        result = {
            'title': self.title,
            'album': self.album,
            'cover': self.cover,
            'download_url': self.download_url,
            'contributors': []
        }
        for c in self.contributors:
            result['contributors'].append({
                'name': c.name,
                'picture': c.picture,
                'fans': c.fans,
                'albums': c.albums
            })
        return result


class DeezerArtist:
    def __init__(self, name, picture, fans, albums):
        self.name = name
        self.picture = picture
        self.fans = fans
        self.albums = albums


def save_song(track):
    song = Song.objects.filter(download_url=track.download_url)
    if not Song.objects.filter(download_url=track.download_url).exists():
        album, _ = Album.objects.get_or_create(
            title=track.album,
            cover=track.cover,
        )
        song = Song.objects.create(
            title=track.title,
            download_url=track.download_url,
            album=album
        )
        print(song)
        for a in track.contributors:
            artist, _ = Artist.objects.get_or_create(
                name=a.name,
                picture=a.picture,
                fans=a.fans,
                albums=a.albums
            )
            song.artists.add(artist)
    else:
        song = song.first()
    return song
