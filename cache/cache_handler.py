import errno
import json
import logging
from pathlib import Path
from sys import platform

logger = logging.getLogger(__name__)

class CacheHandler:
    """
    An abstraction layer for handling the caching
    """

    def get_cached_timeout(self):
        """ get cache timeout """
        raise NotImplementedError

    def get_cached_content(self):
        """ get cache content """
        raise NotImplementedError

    def save_response_to_cache(self, response):
        """
        Save a response of request dictionary object to the cache and return None.
        """
        raise NotImplementedError

    def set_cache_timeout(self, time):
        """
            set cache timeout
        """
        raise NotImplementedError


class CacheFileHandler(CacheHandler):
    """
    Handles reading and writing cached Spotify authorization tokens
    as json files on disk.
    """

    def __init__(self, cache_path=None, username=None):
        if cache_path:
            self.cache_path = cache_path
        else:
            cache_path = ".cache"
            if username is None: username='anonymous'
            if username: cache_path += "-" + str(username)
            self.cache_path = cache_path

        home = Path.home()
        if platform == "win32":
            self.cache_path = home / 'AppData/Roaming/EkilaDownloader/.cache'
        elif platform == "linux":
            self.cache_path = home / '.local/share/EkilaDownloader/.cache'
        elif platform == "darwin":
            self.cache_path = home / '.local/share/EkilaDownloader/.cache'
        self.cache_path = self.cache_path.as_uri().split('///')[1]


    def get_cache_path(self):
        return str(self.cache_path)

    def get_cached_timeout(self):
        timeout_info = None
        try:
            f = open(self.cache_path.absolute())
            timeout_info_string = f.read()
            f.close()
            timeout_info = json.loads(timeout_info_string)
            if isinstance(timeout_info, list):
                timeout_info = timeout_info[len(timeout_info)-1]['expired_at']

        except IOError as error:
            if error.errno == errno.ENOENT:
                logger.debug("cache does not exist at: %s", self.cache_path)
            else:
                logger.warning("Couldn't read cache at: %s", self.cache_path)

        return timeout_info

    def get_cached_content(self):
        content = None
        try:
            f = open(self.cache_path)
            content = f.read()
            f.close()
            content = json.loads(content)

        except IOError as error:
            if error.errno == errno.ENOENT:
                logger.debug("cache does not exist at: %s", self.cache_path)
            else:
                logger.warning("Couldn't read cache at: %s", self.cache_path)
        return content

    def save_response_to_cache(self, response):
        try:
            f = open(self.cache_path, "w")
            f.write(json.dumps(response))
            f.close()
        except IOError:
            logger.warning(
                'Couldn\'t write response to cache at: %s',
                self.cache_path
            )

    def set_cache_timeout(self, time_added):
        try:
            f = open(self.cache_path)
            content = f.read()
            f.close()
            content = json.loads(content)
            if isinstance(content, list):
                content[len(content)-1]['expired_at'] = time_added

        except IOError as error:
            if error.errno == errno.ENOENT:
                logger.debug("cache does not exist at: %s", self.cache_path)
            else:
                logger.warning("Couldn't read cache at: %s", self.cache_path)
