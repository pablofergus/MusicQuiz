import asyncio
import json
import requests
import aiohttp
import random

from quiz.basemodels import Song, Artist, Album
from .exceptions import DeezerApiResponseException


# https://api.deezer.com/track/3135556
# https://api.deezer.com/search?q=bpm_min:120 dur_min:300


async def get_enough_tracks(count, random=False, charts=False, genre=None):
    async with aiohttp.ClientSession() as session:
        if random:
            functions = [get_random_track(session)] * count
        if charts:
            charts = await get_charts(session)
            functions = [get_chart_track(session, charts)] * count
        if genre:
            radio = await get_genre_radio(session, genre)
            count = min(count, len(radio)) - 1
            functions = []
            while count >= 0:
                url = "https://api.deezer.com/track/" + str(radio[count]['id'])
                count -= 1
                functions.append(pop_genre_radio_track(session, url))

        result = await asyncio.gather(*functions)
        await session.close()
        return result


async def get_random_track(session, filters=None):
    search = []
    while not search:
        word = await get_random_word(session)
        search = await get_search(session, word)
    print(word)
    track = await DeezerTrack.create(search[0], session)
    song = save_song(track)
    return song


async def get_chart_track(session, charts, filters=None):
    #charts = await get_charts()
    track = select_track(charts)
    song = save_song(track)
    return song


async def pop_genre_radio_track(session, url, filters=None):
    track = await DeezerTrack.create(await request_and_parse(session, url), session)
    #del tracklist[0]
    song = save_song(track)
    return song


def select_track(tracks, filters=None):
    return random.choice(tracks)


async def get_charts(session, filters=None):
    url = "https://api.deezer.com/editorial/0/charts"
    return (await request_and_parse(session, url))['tracks']['data']


async def get_search(session, query, filters=None):
    url = "https://api.deezer.com/search/?q=" + str(query) + "&order=RATING_DESC"  # "&order=RANKING"
    return (await request_and_parse(session, url))['data']


async def get_genre_radio(session, tracklist, filters=None):  # TODO
    print(tracklist)
    return (await request_and_parse(session, tracklist))['data']


async def get_genre_list():
    url = "https://api.deezer.com/genre/0/radios"
    with aiohttp.ClientSession() as session:
        result = (await request_and_parse(session, url))['data']
        await session.close()
        return result


async def get_random_word(session):
    url = "https://random-word-api.herokuapp.com/word?number=1"
    return (await request_and_parse(session, url))[0]


async def request_and_parse(session, url):
    while True:
        async with session.get(url) as response:
            if response.status is 200:
                result = json.loads(await response.text())
                if 'error' not in result:
                    return result
                else:
                    await asyncio.sleep(1)
            else:
                raise DeezerApiResponseException


class DeezerTrack:

    def __init__(self):
        self.title = ""
        self.album = ""
        self.cover = ""
        self.download_url = ""
        self.contributors = []

    @classmethod
    async def create(cls, track, session):
        self = DeezerTrack()
        self.title = track['title']
        self.album = track['album']['title']
        self.cover = track['album']['cover_big']
        self.download_url = track['preview']
        quota_limit = True
        while quota_limit:
            async with session.get("https://api.deezer.com/artist/" + str(track['artist']['id'])) as response:
                artist = json.loads(await response.text())
                if 'error' not in artist:
                    self.contributors = []
                    self.contributors.append(DeezerArtist(
                        artist['name'],
                        artist['picture_medium'],
                        artist['nb_fan'],
                        artist['nb_album']))
                    quota_limit = False
                else:
                    await asyncio.sleep(1)
        if 'contributors' in track:
            for a in track['contributors']:
                if a['name'] is not self.contributors[0].name:
                    quota_limit = True
                    while quota_limit:
                        async with session.get("https://api.deezer.com/artist/" + str(a['id'])) as response:
                            artist = json.loads(await response.text())
                            if 'error' not in artist:
                                self.contributors.append(Artist(
                                    artist['name'],
                                    artist['picture_medium'],
                                    artist['nb_fan'],
                                    artist['nb_album']))
                                quota_limit = False
                            else:
                                await asyncio.sleep(1)
        return self

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


def save_song(track): #TODO must be async......
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
