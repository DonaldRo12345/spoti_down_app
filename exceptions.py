import enum

"""
    Here we describe our prsonnal
 exception to raise eventual error

"""


class SpotifyCustomerException(Exception):
    def __init__(self, code, msg, reason=None):
        self.code = self.ErrorType()
        self.msg = msg
        self.reason = reason

    def __str__(self):
        return "status code: {0}, msg:{1} , reason: {2}".format(
            self.code, self.msg, self.reason
        )

    class ErrorType(enum.Enum):
        NO_CONTENT = 204
        INTERNAL_SERVER_ERROR = 500
        SUCCESS = 200


class YoutubeDlExtractionError(Exception):
    def __init__(self, message="YoutubeDl failed to download the song!"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class FFmpegNotInstalledError(Exception):
    def __init__(
        self, message="FFmpeg must be installed  [https://ffmpeg.org/download.html]"
    ):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class UrlNotSupportedError(Exception):
    def __init__(self, url, message="URL not supported!"):
        self.url = url
        self.message = f"{message} [{self.url}]"
        super().__init__(self.message)

    def __str__(self):
        return self.message


class InternetConnectionError(Exception):
    def __init__(
        self,
        message="Connection timed out, check you have a stable internet connection!",
    ):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class SongError(Exception):
    def __init__(self, message="Song not found!"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class ComponentError(Exception):
    def __init__(self, message="Component does not exist"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message
