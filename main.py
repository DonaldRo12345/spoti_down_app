import os
from pathlib import Path
from tkinter.messagebox import showerror

from spotipy import Spotify, SpotifyOAuth

from async_controller import AsyncController
from authentication.views.user_form import AuthForm
from custom_tk import App
from settings import settings


def launch_app():
    main_app = AuthForm()
    main_app.mainloop()
    if main_app.is_destroy:
        name = main_app.user_login
        try:
            app = App(name)
            auth_manager = SpotifyOAuth(
            client_id = os.environ.get("SPOTIFY_CLIENT_ID"),
            redirect_uri = os.environ.get("SPOTIPY_REDIRECT_URI"),
            client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET_KEY"),
            scope = settings.SCOPES,
            cache_handler=None,
        )
            sp_client = Spotify(client_credentials_manager=auth_manager)
            async_controller = AsyncController(client_api=sp_client)
            async_controller.register_view(app)
            app.mainloop()
        except Exception as err:
            showerror("Erreur", str(err))


def set_env_var():
    env_file = Path(".env")
    if env_file.exists():
        print("env file found : ", env_file)
        with env_file.open("r") as f:
            env_var_list = f.readlines()
            for env_var in env_var_list:
                key, value = env_var.split("=")
                value = value.replace('"', "").replace("\n", "")
                os.environ[key] = value
    else:
        print("env file not exists")


# -------launch application)
if __name__ == "__main__":
    set_env_var()
    launch_app()
