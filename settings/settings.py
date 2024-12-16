import os
from enum import Enum
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

READ_DOT_ENV_FILE = os.environ.get("READ_DOT_ENV_FILE", None)

if READ_DOT_ENV_FILE:
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with env_file.open("r") as f:
            env_var_list = f.readlines()
            for env_var in env_var_list:
                key, value = env_var.split("=")
                value = value.replace('"', "").replace("\n", "")
                os.environ[key] = value


# ------------ wazateam account --------------------------------
SPOTIPY_REDIRECT_URI = "https://stackoverflow.com/"
SCOPES = "playlist-modify-public, playlist-modify-private, user-top-read, user-read-recently-played"
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", None)
SPOTIFY_CLIENT_SECRET_KEY = os.environ.get("SPOTIFY_CLIENT_SECRET_KEY", None)
USER_ID = os.environ.get("USER_ID", None)

STEEVE_SPOTIPY_REDIRECT_URI = SPOTIPY_REDIRECT_URI
STEEVE_SPOTIFY_CLIENT_ID = SPOTIFY_CLIENT_ID
STEEVE_SPOTIFY_CLIENT_SECRET_KEY = SPOTIFY_CLIENT_SECRET_KEY
STEEVE_USER_ID = USER_ID


class LoadingState(Enum):
    """Downloading state define"""

    LOADING: str = "loading"
    STOP: str = "stop"
