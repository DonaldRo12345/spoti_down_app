import unittest

from settings import settings
from spotify import APIConfig
from spotify import SpotifyCustomer


def get_api_configuration():
    """spotify api keys"""

    conf = APIConfig
    conf.SPOTIFY_CLIENT_ID = settings.STEEVE_SPOTIFY_CLIENT_ID
    conf.USER_ID = settings.STEEVE_USER_ID
    conf.SPOTIPY_REDIRECT_URI = settings.STEEVE_SPOTIPY_REDIRECT_URI
    conf.SPOTIFY_CLIENT_SECRET_KEY = settings.STEEVE_SPOTIFY_CLIENT_SECRET_KEY
    conf.scopes = settings.SCOPES
    return conf
class TestSpotiyfAPI(unittest.TestCase):
    """Testing spotify class"""

    customer = SpotifyCustomer(config=get_api_configuration())

    def test_search(self):
        result = self.customer.search("Dzanum")
        assert isinstance(result, list)
        assert len(result) == 1

    def test_current_user(self):
        result = self.customer.get_current_user()
        assert result is not None
        assert result['display_name'] == 'defol'
        assert result['type'] == 'user'
        assert result['id'] is not None

    def test_search_song(self):
        result = self.customer.search_song("Family Affair")
        assert result is not None
        assert len(result) == 3
        assert result[0] == 'https://open.spotify.com/track/3aw9iWUQ3VrPQltgwvN9Xu'
        assert result[1] == "Mary J. Blige"
        assert result[2] == "Family Affair"
