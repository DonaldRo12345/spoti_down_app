import asyncio
import os
import threading
import tkinter as tk
from abc import ABC, abstractmethod
from shutil import move
from tkinter import messagebox

import aiohttp
import customtkinter
import yt_dlp
from ffmpy import FFmpeg, FFRuntimeError
from yt_dlp.utils import DownloadError

from crypto import SimpleEncryption
from downloader import DownloaderUtils
from exceptions import FFmpegNotInstalledError
from type import Format, Quality
from utils import PathHolder, check_ffmpeg, safe_path_string

SEMAPHORE_LIMIT = 4
MAX_RETRIES = 3


class SongMetadata:
    def __init__(
            self,
            id,
            name,
            album_name,
            release_date,
            artist_names,
            disc_number,
            track_number,
            album_track_count,
            isrc,
            url,
            cover_art_url
    ):
        self.id = id
        self.name = name
        self.album_name = album_name
        self.release_date = release_date
        self.artist_names = artist_names
        self.disc_number = disc_number
        self.track_number = track_number
        self.album_track_count = album_track_count
        self.isrc = isrc
        self.url = url
        self.cover_art_url = cover_art_url

    def __str__(self):
        return f"{self.artist_names[0]} - {self.name}"


class BaseController(ABC):

    @abstractmethod
    def register_view(self, view):
        pass


class AsyncController(BaseController):

    SPOTIFY_PLAYLIST_URI = "https://open.spotify.com/playlist/"
    SPOTIFY_TRACK_URI = "https://open.spotify.com/track/"
    SPOTIFY_ALBUM_URI = "https://open.spotify.com/album/"
    SPOTIFY_URL = "https://open.spotify.com/"

    def __init__(self, client_api):
        self.group = None
        self.retry = 3
        self.ffmpeg_location = "ffmpeg"
        self.downloaded_cover_art = {}
        self.download_folder = os.getcwd() + "/EkilaDownloader"
        self.client_api = client_api
        self.view = None
        self.quality = Quality.BEST
        self.download_format = Format.MP3
        self.path_holder = PathHolder(downloads_path=os.getcwd() + "/EkilaDownloader")
        self.semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)
        self.total_downloads_count = 0

        self.utils = DownloaderUtils()

        if not check_ffmpeg() and self.ffmpeg_location == "ffmpeg":
            # raise FFmpegNotInstalledError
            print("FFmpeg n'est pas installé, des erreurs peuvent survenir lors de l'exécution du programme.")

    def register_view(self, view):
        view.set_controller(self)
        self.view = view


    async def fetch_songs(self, spotify_url):
        try:
            url_parts = spotify_url.split("/")[-2:]
            spotify_type, spotify_id = url_parts[0], url_parts[1].split("?")[0]

            songs_metadata = []

            if spotify_type == "playlist":
                playlist = self.client_api.playlist(spotify_id)
                results = playlist["tracks"]
                tracks = results["items"]

                while results["next"]:
                    results = self.client_api.next(results)
                    tracks.extend(results["items"])

                for item in tracks:
                    track = item["track"]
                    songs_metadata.append(self._extract_song_metadata(track))
            elif spotify_type == "track":
                track = self.client_api.track(spotify_id)
                songs_metadata.append(self._extract_song_metadata(track))
            elif spotify_type == "album":
                album = self.client_api.album(spotify_id)
                tracks = album["tracks"]["items"]
                for track in tracks:
                    track["album"] = {
                        "name": album["name"],
                        "release_date": album["release_date"],
                        "images": album["images"],
                        "total_tracks": album["total_tracks"]
                    }
                    songs_metadata.append(self._extract_song_metadata(track))
            else:
                messagebox.showerror(
                    "Erreur",
                    f"Type d'URL Spotify non pris en charge : {spotify_type}"
                )

            return songs_metadata
        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de récupérer les chansons {e}"
                f"Veillez à ce que l'URL soit correcte."
            )
            return []

    def _extract_song_metadata(self, track):
        """Extrait les métadonnées d'une piste."""
        return SongMetadata(
            id=track["id"],
            name=track["name"],
            album_name=track["album"]["name"],
            release_date=track["album"]["release_date"],
            artist_names=[artist["name"] for artist in track["artists"]],
            disc_number=track["disc_number"],
            track_number=track["track_number"],
            album_track_count=track["album"].get("total_tracks", 0),
            isrc=track.get("external_ids", {}).get("isrc", ""),
            url=track["external_urls"]["spotify"],
            cover_art_url=track["album"]["images"][0]["url"] if track["album"]["images"] else ""
        )

    async def download_song(self, session, song_metadata):
        """Télécharge une chanson via yt-dlp."""
        def progress_hook(d):
            if d["status"] == "downloading":
                percentage = float(d.get("downloaded_bytes", 0)) / float(d.get("total_bytes", 1)) * 100
                self.view.after(0, self.update_song_progress, song_metadata.name, percentage)

                self.view.after(0, self.update_global_progress)
            elif d["status"] == "finished":
                self.view.after(0, self.update_song_progress, song_metadata.name, 100)
                self.view.completed_songs += 1
                self.view.after(0, self.update_global_progress)
        try:
            output_temp = f"{str(self.path_holder.get_temp_dir())}/{song_metadata}.%(ext)s"

            if os.path.exists(
                    f"{self.download_folder}/{song_metadata.artist_names[0]} - {song_metadata.name}.mp3"
            ):
                print(f"{song_metadata.name} already downloaded")
                return

            options = {
                "format": "bestaudio/best",
                "outtmpl": output_temp,
                "restrictfilenames": True,
                "ignoreerrors": True,
                "nooverwrites": True,
                "noplaylist": True,
                "prefer_ffmpeg": True,
                "quiet": True,
                "no_warnings": True,
                "progress_hooks": [progress_hook],
                "write-thumbnail": True,
                "external_downloader_args": ["-loglevel", "panic"],
                "retries": 3,
                "sleep_interval_requests": 1,
                "sleep_interval": 1.5,
                "socket_timeout": 120,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": self.download_format,
                        "preferredquality": self.quality,
                    },
                ],
                "postprocessor_args": [
                    "-write_id3v1",
                    "1",
                    "-id3v2_version",
                    "3",
                    "-metadata",
                    f"title={song_metadata.name}",
                    "-metadata",
                    f"album={song_metadata.album_name}",
                    "-metadata",
                    f"date={song_metadata.release_date}",
                    "-metadata",
                    f'artist={", ".join(artist.upper() for artist in song_metadata.artist_names)}',
                    "-metadata",
                    f"disc={song_metadata.disc_number}",
                    "-metadata",
                    f"track={song_metadata.track_number}/{song_metadata.album_track_count}",
                    "-metadata",
                    f"isrc={song_metadata.isrc}",
                ],
            }

            output = (
                    self.path_holder.get_download_directory()
                    / f"{self.utils.sort_directory(song_metadata, self.group)}"
                    / safe_path_string(f"{str(song_metadata)}.{self.download_format}")
            )

            output_temp = output_temp.replace("%(ext)s", self.download_format)

            if self.download_format == Format.MP3:
                options["postprocessor_args"].append("-codec:a")
                options["postprocessor_args"].append("libmp3lame")

            if self.ffmpeg_location != "ffmpeg":
                options["ffmpeg_location"] = self.ffmpeg_location

            retries = 0

            while retries < MAX_RETRIES:
                try:
                    with yt_dlp.YoutubeDL(options) as ydl:
                        search_result = f"ytsearch:{song_metadata.artist_names[0]} - {song_metadata.name} audio"
                        result = await asyncio.to_thread(ydl.download, [search_result])
                        print(f"Téléchargement réussi pour {song_metadata.artist_names[0]}-{song_metadata.name}")
                    break
                except DownloadError as e:
                    retries += 1
                    print(f"Erreur de téléchargement (tentative {retries}/{MAX_RETRIES}) pour {song_metadata.artist_names[0]}-{song_metadata.name} : {e}")
                    if retries >= MAX_RETRIES:
                        print(f"Abandon du téléchargement pour {song_metadata.artist_names[0]}-{song_metadata.name} après {MAX_RETRIES} tentatives.")
                        return

                except Exception as e:
                    print("inside exception")
                    retries += 1
                    print(f"Erreur inconnue (tentative {retries}/{MAX_RETRIES}) pour {song_metadata.artist_names[0]}-{song_metadata.name} : {e}")
                    if retries >= MAX_RETRIES:
                        print(f"Abandon du téléchargement pour {song_metadata.artist_names[0]}-{song_metadata.name} après {MAX_RETRIES} tentatives.")
                        return

            if not os.path.exists(output_temp):
                print(f"Fichier temporaire manquant pour {song_metadata.artist_names[0]}-{song_metadata.name}.")
                return


            cover_art_name = f"{song_metadata.album_name} - {song_metadata.artist_names[0]}"

            if cover_art_name in self.downloaded_cover_art:
                cover_art = self.downloaded_cover_art[cover_art_name]
            else:
                cover_art = await self.path_holder.download_file(
                    song_metadata.cover_art_url, extension="jpg"
                )
                self.downloaded_cover_art[cover_art_name] = cover_art

            if not os.path.exists(cover_art):
                print(f"URL de l'image de couverture manquante pour {song_metadata.name}: {cover_art}.")
            else:
                print(f"URL de l'image de couverture trouvée pour {song_metadata.name}: {cover_art}.")

            try:
                ffmpeg = FFmpeg(
                    executable=self.ffmpeg_location,
                    inputs={
                        str(output_temp): None,
                        str(cover_art): None,
                    },
                    outputs={
                        str(
                            output
                        ): "-loglevel quiet -hide_banner -y -map 0:0 -map 1:0 -c copy -id3v2_version 3 "
                        '-metadata:s:v title="Album cover" -metadata:s:v comment="Cover (front)" '
                    },
                )
                ffmpeg.run()
            except Exception as e:
                print(f"Commande ffmpeg échouée: {e.cmd}")
                print(f"Sortie d'erreur: {e.stderr}")
            else:
                self.total_downloads_count += 1

            safe_remove(output_temp)

        except Exception as e:
            print(f"Erreur lors du téléchargement de {song_metadata.name} : {e}")
            raise Exception
        finally:
            self.view.completed_songs += 1
            self.update_song_progress(song_metadata.name, 100)
            # self.view.after(0, self.update_global_progress)

    async def download_with_semaphore(self, session, song_name):
        semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)
        async with semaphore:
            await self.download_song(session, song_name)

    async def download_all_songs(self, songs):
        """Télécharge toutes les chansons simultanément avec une limite."""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for _i, song in enumerate(songs, 1):
                self.view.progress_data[song] = 0
                self.add_song_widgets(song, _i)
                tasks.append(self.download_with_semaphore(session, song))
            await asyncio.gather(*tasks)

    def add_song_widgets(self, song, number):
        song_label = tk.Label(
            self.view.inner_frame,
            text=f"{number}. {song.artist_names[0]} - {song.name}",
            fg="white",
            bg="#2e2e2e",
            font=("", 9, "italic"),
        )
        song_label.pack(anchor="w", pady=5, padx=5)
        progress = customtkinter.CTkProgressBar(
            self.view.inner_frame,
            height=7,
            width=775,
            progress_color="#3b8ed0"
        )
        progress.set(0)

        progress.pack(pady=5, padx=5)

        self.view.song_labels[song.name] = song_label
        self.view.progress_bars[song.name] = progress

    def show_song_widgets(self):
        for song_name, song_label in self.view.song_labels.items():
            song_label.pack(anchor="w", pady=5, padx=5)
            progress = self.view.progress_bars[song_name]
            progress.pack(pady=5, padx=5)

    def update_song_progress(self, song_name, progress_value):
        self.view.progress_bars[song_name].set(progress_value/100)


    def update_global_progress(self):

        sum_of_progress = sum(
            float(progress.get()) for progress in self.view.progress_bars.values()
        )
        total_percent = (sum_of_progress / self.view.total_songs)
        total_percent_between_zero_and_one = total_percent
        self.view.download_progressbar.set(total_percent_between_zero_and_one)
        self.view.text_percent.config(
            text=f"{self.view.total_songs} Chansons: {total_percent:.2%}"
        )

    def start_download(self):
        playlist_url = self.view.down_path.get()
        if not playlist_url:
            messagebox.showwarning(
                "Attention",
                "Veuillez entrer une URL de playlist."
            )
            return

        def run_async_download():
            asyncio.run(self.async_download_task(playlist_url))

        threading.Thread(target=run_async_download, daemon=True).start()
        

    async def async_download_task(self, url):
        if self.view.progress_bars and self.view.song_labels:
            for label in self.view.song_labels.values():
                label.destroy()
            for progress in self.view.progress_bars.values():
                progress.destroy()

            self.view.song_labels = {}
            self.view.progress_bars = {}

            self.view.total_songs = 0
            self.view.completed_songs = 0
            self.total_downloads_count = 0
            
            self.view.download_progressbar.set(0)
            

        if (
                self.SPOTIFY_URL in url
        ):
            decrypt_word = url
        else:
            decrypt_word = SimpleEncryption(url=None)._decrypt_url(url)  # noqa: SLF001
        self.initialise_down_entry()
        songs_metadata = await self.fetch_songs(decrypt_word)
        if songs_metadata:
            self.view.total_songs = len(songs_metadata)
            self.view.text_percent.config(
                text=f"{self.view.total_songs} Chansons: 0.0%"
            )
            os.makedirs(self.download_folder, exist_ok=True)
            await self.download_all_songs(songs_metadata)
            messagebox.showinfo(
                "Téléchargement terminé",
                f"{self.total_downloads_count} chansons ont été téléchargées avec succès !"
            )

    def initialise_down_entry(self):
        try:
            self.view.down_path.set("")
            self.view.link_entry.delete(0, tk.END)
        except Exception as e:
            print("Une erreur est survenu: ", e)


def safe_remove(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
    else:
        print(f"Le fichier {file_path} n'existe pas et ne peut pas être supprimé.")