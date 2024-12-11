import time
from enum import Enum
from typing import Any, Dict, List

import spotipy
from spotipy.cache_handler import MemoryCacheHandler
from spotipy.oauth2 import SpotifyOAuth

from cache.cache_handler import CacheFileHandler
from tracks import Track, TrackDto
from type import Type


class APIConfig(Enum):
    """Api configuration"""

    SPOTIPY_REDIRECT_URI: str
    SPOTIFY_CLIENT_ID: str
    SPOTIFY_CLIENT_SECRET_KEY: str
    USER_ID: str
    scopes: str


class SpotifyUtils:
    @staticmethod
    def __pack_album(album) -> list:
        tracks = []
        for track in album["tracks"]["items"]:
            track_data = track
            track_data["album"] = album
            tracks.append(Track(track_data))
        return tracks

    @staticmethod
    def __pack_playlist(playlist, is_playlist_panel: bool = False) -> list:
        tracks: List[Any] = []
        tracks_temp = [track["track"] for track in playlist["tracks"] if track]
        for track_data in tracks_temp:
            if track_data:
                if is_playlist_panel:
                    tracks.append(TrackDto(track_data))
                else:
                    track_data[
                        "playlist"
                    ] = f"{playlist['name']} - \
                        {playlist['owner']['display_name']}"
                    tracks.append(Track(track_data))
        return tracks


class SpotifyCustomer:
    """
    my spotify customer use
    to fecth spotify data

    complete those keys with yours or setup it
    on env vars
    """

    def __init__(self, config: APIConfig) -> None:
        self.auth_manager = SpotifyOAuth(
            client_id=config.SPOTIFY_CLIENT_ID,
            client_secret=config.SPOTIFY_CLIENT_SECRET_KEY,
            redirect_uri=config.SPOTIPY_REDIRECT_URI,
            scope=config.scopes,
            cache_handler=None,
        )
        self.sp_utils: SpotifyUtils = SpotifyUtils()
        self.rest_cache: CacheFileHandler = CacheFileHandler(
            cache_path=None, username=None
        )

        token_info: Dict = self.auth_manager.get_access_token()
        self.user_id: str = config.USER_ID

        if isinstance(token_info, dict):
            self.auth_manager.cache_handler = MemoryCacheHandler(token_info=token_info)
            self.auth_manager.cache_handler.save_token_to_cache(token_info=token_info)
            self.client = spotipy.Spotify(auth_manager=self.auth_manager)

    def is_token_expired(self) -> bool:
        now = int(time.time())
        cache_handler = self.client.auth_manager.cache_handler
        time_token = cache_handler.get_cached_token()["expires_at"]
        return time_token - now < 60

    def is_cache_expired(self) -> bool:
        try:
            now = int(time.time())
            return self.rest_cache.get_cached_timeout() - now == 0
        except Exception as error:
            raise error

    def get_playlist_from_api(self) -> list:
        try:
            if not self.is_token_expired():
                user_playlist = []
                playlists = self.client.user_playlists(self.user_id)
                while playlists:
                    for i, playlist in enumerate(playlists["items"]):
                        user_playlist.append(
                            {
                                "name": playlist["name"],
                                "id": playlist["id"],
                                "uri": playlist["external_urls"]["spotify"],
                            }
                        )
                    if playlists["next"]:
                        playlists = self.client.next(playlists)
                    else:
                        playlists = None
                user_playlist.append({"expired_at": 1209600})
                self.rest_cache.save_response_to_cache(user_playlist)
                return user_playlist
        except Exception:
            return []

    def get_user_plalists(self) -> list:
        if not self.is_token_expired():
            user_playlist = self.get_playlist_from_api()
            return user_playlist
        return []


    def get_specific_albums_tracks(self, album_id) -> Any:
        if not self.is_token_expired():
            albums = self.client.album_tracks(album_id, limit=50, offset=0, market=None)
            return albums

    def get_artist(self, name) -> str:
        if not self.is_token_expired():
            results = self.client.search(q="artist:" + name, type="artist")
            items = results["artists"]["items"]
            if len(items) > 0:
                return items[0]
            return None

    def show_artist_albums(self, artist) -> None:
        if not self.is_token_expired():
            albums = []
            results = self.client.artist_albums(artist["id"], album_type="album")
            albums.extend(results["items"])
            while results["next"]:
                results = self.client.next(results)
                albums.extend(results["items"])
            seen = set()
            albums.sort(key=lambda album: album["name"].lower())

            for album in albums:
                name = album["name"]
                if name not in seen:
                    seen.add(name)

    def get_current_user(self) -> Any:
        try:
            current_user = self.client.current_user()
            return current_user
        except Exception as err:
            raise err

    def get_user(self) -> Any:
        user = self.client.user(self.user_id)
        if user is not None:
            return user

    def get_playlist_items(self, playlist_id) -> str:
        playlist_items = self.client.playlist_items(
            playlist_id,
            fields=None,
            limit=100,
            offset=0,
            market=None,
            additional_types=("track", "episode"),
        )
        return playlist_items["items"]

    def search_song(self, query) -> tuple:
        song = self.client.search(query, limit=1, offset=0, type="track")
        if song is not None:
            try:
                return (
                    song["tracks"]["items"][0]["external_urls"]["spotify"],
                    song["tracks"]["items"][0]["artists"][0]["name"],
                    song["tracks"]["items"][0]["name"],
                )
            except KeyError:
                pass
        return None, None, None

    def search(self, query, query_type=Type.TRACK) -> list:
        results = self.client.search(q=query, limit=1, type=query_type)

        if len(results[query_type + "s"]["items"]) > 0:
            if query_type == Type.TRACK:
                return [Track(results[Type.TRACK + "s"]["items"][0])]
            elif query_type == Type.ALBUM:
                return self.sp_utils._SpotifyUtils__pack_album(
                    self.client.album(results[Type.ALBUM + "s"]["items"][0]["id"])
                )
            elif query_type == Type.PLAYLIST:
                return self._get_playlist_tracks(
                    results[Type.PLAYLIST + "s"]["items"][0]["id"]
                )
        else:
            return []

    def link(self, query) -> list:
        try:
            if "/track/" in query:
                return [Track(self.client.track(query))]
            elif "/album/" in query:
                return self.sp_utils._SpotifyUtils__pack_album(self.client.album(query))
            elif "/playlist/" in query:
                return self._get_playlist_tracks(query)
            else:
                return []
        except Exception:
            return []

    def is_track_or_playlist(self, query) -> str:
        if "/track/" in query:
            return "TRACK"
        elif "/playlist/" in query:
            return "PLAYLIST"

    def _get_playlist_tracks(
        self, playlist_id, is_playlist_panel: bool = False
    ) -> list:
        playlist = self.client.playlist(playlist_id)
        results = playlist["tracks"]
        tracks = results["items"]
        while results["next"]:
            results = self.client.next(results)
            tracks.extend(results["items"])

        playlist["tracks"] = tracks
        return self.sp_utils._SpotifyUtils__pack_playlist(playlist, is_playlist_panel)

    def _get_playlist_name(self, playlist_id) -> str:
        return self.client.playlist(playlist_id)["name"]

    def create_playlists(self, playlist_name: str) -> bool:
        all_playlist = self.get_user_plalists()
        is_created = False
        for i in range(0, len(all_playlist) - 1):
            if all_playlist[i]["name"] == playlist_name:
                is_created = True
                break

        if not is_created:
            self.client.user_playlist_create(self.user_id, playlist_name, public=True)
        return is_created

    def is_playlist_exist(self, playlist_name: str) -> tuple:
        all_playlist = self.get_user_plalists()
        track, exist = None, False
        for track in all_playlist:
            if track["name"] == playlist_name:
                track, exist = track, True
                break
        return track, exist

    def is_song_exist(self, playlist_title: str, song_uri: str) -> bool:
        track, exist = self.is_playlist_exist(playlist_title)
        is_uri: bool = False
        if track["name"] == playlist_title:
            items = self.client.playlist(
                playlist_id=track["id"], additional_types=("track",)
            )
            for song in items["tracks"]["items"]:
                if song_uri == song["track"]["external_urls"]["spotify"]:
                    is_uri = True
                    break
        return is_uri

    def add_items_in_playlist(self, playlist_name: str, tracks: list) -> None:
        if not self.is_token_expired():
            track, is_exist = self.is_playlist_exist(playlist_name)
            if is_exist:
                self.client.playlist_add_items(track["id"], tracks)

    async def send_one_song_to_playlist(self, song_uri: str, playlist_title):
        tab_song: List[str] = []
        tab_song.append(song_uri)
        try:
            if playlist_title is not None:
                self.add_items_in_playlist(
                    playlist_name=playlist_title, tracks=tab_song
                )
        except Exception as error:
            raise error

    def delete_playlist(self, playlist_id: str) -> None:
        self.client.user_playlist_unfollow(
            user=self.client.current_user()["id"], playlist_id=playlist_id
        )


if __name__ == "__main__":
    pass
