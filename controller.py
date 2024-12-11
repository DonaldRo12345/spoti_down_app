import asyncio
import csv
import logging
import os
import time
import tkinter
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
from pathlib import Path
from tkinter.filedialog import askdirectory, askopenfilename, askopenfilenames
from tkinter.messagebox import askyesno, showinfo, showwarning
from typing import Tuple

import customtkinter

from crypto import SimpleEncryption
from downloader import Downloader
from excel_controller import ExcelFileHandler
from exceptions import ComponentError
from metadata import XlsMeta
from settings.settings import LoadingState as load
from spotify import SpotifyCustomer
from type import Format, Quality
from utils import PathHolder, Utils


class Controller:
    SPOTIFY_PLAYLIST_URI = "https://open.spotify.com/playlist/"
    SPOTIFY_TRACK_URI = "https://open.spotify.com/track/"

    logging.basicConfig(
        format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
        filename="error.log",
        level=logging.DEBUG,
        datefmt="%m/%d/%Y %I:%M:%S %p",
    )

    global logger

    num_track: int = 1
    meta_start: int = 3
    contrib_start: int = 2
    len_meta: int = 0
    len_contrib: int = 0
    is_song_loading: bool
    logger = logging.getLogger(__name__)

    def __init__(self, view, sp_client: SpotifyCustomer):
        self.view = view
        self.sp_client = sp_client
        self.search_songs = []
        self.loading_state = None
        self.excel_handler = ExcelFileHandler(file_dir="static/METADATA.xlsx")

    def create_playlist(self, playlist_name):
        """permit a user to create a playlist"""

        return self.sp_client.create_playlists(playlist_name)

    def open_input_dialog_for_volume_number(self):
        dialog = customtkinter.CTkInputDialog(
            text="Entrer le nom de l'album:", title="Nom album"
        )
        return dialog.get_input()

    def delete_playlist(self, playlist_id):
        """permit a user to delete a playlist"""

        try:
            if playlist_id:
                entry = askyesno(
                    title="Suppression",
                    message="Voulez vous supprimer cette playlist ?",
                )
                if entry:
                    self.sp_client.delete_playlist(playlist_id)
                    self.sp_client.get_playlist_from_api()
                    asyncio.run(self.checkbox_playlist_output())
            else:
                showwarning("Warning", "Choisir une playlist")
        except Exception as error:
            raise error

    async def check_song_exist_in_playlist(self, song_uri: str, playlist_title: str):
        """check if a song exist in a playlist"""

        return (
            self.sp_client.is_song_exist(playlist_title, song_uri),
            song_uri,
        )

    def delete_cache(self):
        """delete cache file and actualise app"""

        try:
            cache_path = self.sp_client.rest_cache.get_cache_path()
            my_file = Path(cache_path)
            if my_file.is_file():
                os.remove(cache_path)
                if self.view.scrollable_sons_list:
                    asyncio.run(self.checkbox_playlist_output())
        except Exception as error:
            raise error

    def get_playlist_from_api(self):
        """get playlist to catch update made"""

        try:
            self.sp_client.get_playlist_from_api()
        except Exception as error:
            raise error
        return

    def open_file(self):
        """get csv file path"""

        filetypes = (("csv files", "*.csv"), ("All files", "*.csv"))
        file_path = askopenfilename(title="ouvrir un fichier", filetypes=filetypes)
        return file_path

    def open_many_file(self):
        filetypes = (("csv files", "*.csv"), ("All files", "*.csv"))
        file_path = askopenfilenames(title="ouvrir un fichier", filetypes=filetypes)
        file_list = list(file_path)
        return " ; ".join(file_path), file_list

    def open_many_mp3_file(self):
        filetypes = (("mp3 files", "*.mp3"), ("All songs files", "*.mp3"))
        file_path = askopenfilenames(title="Choisir vos sons", filetypes=filetypes)
        return list(file_path)

    def open_file_mp3(self):
        """get mp3 file path"""

        filetypes = (("mp3 files", "*.mp3"), ("All songs files", "*.mp3"))
        file_mp3_path = askopenfilename(
            title="ouvrir un fichier audio", filetypes=filetypes
        )
        return file_mp3_path

    async def read_sng(self, query: str):
        """search a song on spotify and return song link"""

        spotify_link, artist_name, song_title = self.sp_client.search_song(query)
        if query is None or spotify_link is None:
            pass
        else:
            self.search_songs.append(
                {"song_link": spotify_link, "artist": artist_name, "title": song_title}
            )
        return spotify_link

    async def read_unique_file(self, file_path):
        """read song on csv file and print response on screen"""

        song_title, count = set(), 0
        self.search_songs = []
        progress = 0
        if file_path:
            with open(file_path, mode="r", encoding="utf8", errors="ignore") as file:
                csvreader = csv.reader(file)
                for row in csvreader:
                    new_row = row[0].split(";")
                    if new_row[1] != "Listen num":
                        song_title.add(new_row[1])

            self.view.progressbar.configure(determinate_speed=1)
            for song in song_title:
                try:
                    await self.read_sng(song)
                    if self.view.textbox_csv:
                        self.view.textbox_csv.insert(
                            tkinter.INSERT, "\t" + str(count) + ". " + song + "\n"
                        )
                        self.view.update()
                        self.view.progressbar.start()
                        progress = 1 / len(song_title) + progress
                        self.view.progressbar.set(progress)
                        count += 1
                except Exception:
                    pass
            self.view.progressbar.stop()
            showinfo("Success", "Opération terminée")
            self.initialise_entry()
        else:
            showwarning("message", "Veuillez choisir un fichier!")

    async def run_async_pool(self, file_list: list):
        if len(file_list) > 0:
            if len(file_list) == 1:
                await self.read_unique_file(file_list[0])
            elif len(file_list) >= 2:
                file = Utils.make_copy_file(file_list)
                await self.read_unique_file(file)
        else:
            showwarning("Attention", "Veuillez choisir un fichier csv!")

    def initialise_entry(self):
        """initialise csv entries"""

        try:
            self.view.file_path.set("")
            self.view.csv_entry.delete(0, tkinter.END)
            self.view.textbox_csv.delete("0.0", "end")
            self.view.progressbar.set(0)
        except:
            raise ComponentError

    async def song_panel(self):
        """print all song extract from csv in transfert song panel"""

        try:
            self.check_var = tkinter.StringVar()
            self.header = customtkinter.CTkCheckBox(
                self.view.scrollable_sons_frame,
                text="Liste sons",
                variable=self.check_var,
                command=self.select_checkboxes,
                onvalue="on",
                offvalue="off",
            )
            self.header.grid(row=0, column=0, pady=(0, 10), sticky="nw")

            self.scrollable_frame_switches = []
            self.checkbox_value = tkinter.StringVar()

            for i, songs in enumerate(self.search_songs):
                await self.checkbox_song_output(songs, i)
                self.view.update()
                self.is_song_loading = True
                if i + 1 == len(self.search_songs):
                    self.is_song_loading = False
            if not self.is_song_loading:
                showinfo(
                    title="Info", message="Chargement terminé, proceder aux transfert.."
                )

        except Exception as err:
            raise err

    async def checkbox_song_output(self, songs, index):
        try:
            checkbox = customtkinter.CTkCheckBox(
                self.view.scrollable_sons_frame,
                text=songs["artist"] + "- " + songs["title"],
                variable=self.checkbox_value,
                onvalue=songs["song_link"],
                offvalue="off",
            )
            checkbox.grid(row=index + 1, column=0, pady=(0, 10), sticky="nw", padx=30)
            self.scrollable_frame_switches.append(checkbox)
        except Exception as error:
            raise error

    async def select_and_deselect(self):
        self.items_selected = []
        self.current_header_state = self.check_var.get()

        try:
            if self.current_header_state == "on":
                for checkbox in self.scrollable_frame_switches:
                    await Utils.select_checkbox(checkbox)
                    self.items_selected.append(self.checkbox_value.get())
                    self.view.update()
                    self.loading_state = load.LOADING.value
                self.loading_state = load.STOP.value
            elif self.current_header_state == "off":
                for checkbox in self.scrollable_frame_switches:
                    await Utils.deselect_checkbox(checkbox)
                    self.view.update()
                    self.loading_state = load.LOADING.value
                self.loading_state = load.STOP.value
        except RuntimeError:
            raise Exception("Entendez la fin du chargement des sons")

    def select_checkboxes(self):
        asyncio.run(self.select_and_deselect())

    async def checkbox_playlist_output(self):
        """print all user's playlist in transfert song panel"""

        all_playlist = self.sp_client.get_user_plalists()
        self.playlist_var = tkinter.StringVar()
        self.scrollable_playlist_switches = []

        for idx in range(0, len(all_playlist) - 1):
            await self.create_playlist_checkbox(all_playlist[idx], idx)
            self.view.update()

    async def create_playlist_checkbox(self, value, idx):
        """create unique playlist"""

        checkbox = customtkinter.CTkRadioButton(
            self.view.scrollable_sons_list,
            text=value["name"]
            .encode(encoding="ascii", errors="ignore")
            .decode("utf-8"),
            value=value["id"],
            variable=self.playlist_var,
            command=self.selected_playlist,
        )
        checkbox.grid(row=idx, column=0, pady=(0, 10), sticky="nw", padx=30)
        self.scrollable_playlist_switches.append(checkbox)

    def selected_playlist(self):
        print("selected playlist:: ", self.playlist_var.get())

    def get_playlist_id(self):
        return self.playlist_var.get()

    def get_selected_playlist(self):
        """get selected playlist title"""

        playlist_id = self.playlist_var.get()
        playlist_name = None
        if playlist_id:
            playlist_name = self.sp_client._get_playlist_name(playlist_id)
            return playlist_name
        return playlist_name

    def copy_link(self):
        """copy a playlist link"""

        if self.playlist_var.get():
            playlist_uri = self.SPOTIFY_PLAYLIST_URI + self.playlist_var.get()
            encrypted_link = SimpleEncryption(url=playlist_uri)._encrypt_url()
            Utils.copy_paste_text(self.view, encrypted_link)
            showinfo("Info", "copier avec succès")

    async def transfert_songs(self):
        """transfert selected songs in a playlist"""

        progress = 0
        playlist_name = self.get_selected_playlist()

        try:
            if self.loading_state == load.STOP.value:
                if len(self.items_selected) > 0:
                    if playlist_name:
                        self.view.progressbar.configure(determinate_speed=1)
                        for song in self.items_selected:
                            (
                                is_exist,
                                song_url,
                            ) = await self.check_song_exist_in_playlist(
                                song, playlist_name
                            )
                            if not is_exist:
                                self.view.progressbar.start()
                                self.view.progressbar.stop()
                                await self.sp_client.send_one_song_to_playlist(
                                    song_uri=song_url, playlist_title=playlist_name
                                )
                                self.view.update()
                                progress = 1 / len(self.items_selected) + progress
                                self.view.progressbar.set(progress)
                            else:
                                self.view.progressbar.start()
                                self.view.progressbar.stop()
                                self.view.update()
                                progress = 1 / len(self.items_selected) + progress
                                self.view.progressbar.set(progress)

                        self.view.progressbar.stop()
                        self.view.progressbar.set(0)
                        self.copy_link()
                        showinfo("Success", f"transfert terminée")
                        self.header.deselect()
                        for checkbox in self.scrollable_frame_switches:
                            await Utils.deselect_checkbox(checkbox)
                            self.view.update()

                    else:
                        showwarning("Warning", "Choisir une playlist")
                else:
                    showwarning("Warning", "Choisir tous les sons")

            elif self.loading_state == load.LOADING.value:
                showwarning(
                    "Warning",
                    "transfert impossible veuillez attendre le chargement des sons",
                )

        except Exception as error:
            raise error

    def initialise_download_textbox(self):
        try:
            self.view.textbox.delete("0.0", "end")
        except ComponentError as error:
            raise error

    def download_one_song(self, url) -> None:
        downloader = Downloader(
            sp_client=self.sp_client,
            quality=Quality.BEST,
            download_format=Format.MP3,
            path_holder=PathHolder(downloads_path=os.getcwd() + "/EkilaDownloader"),
            logger=logger,
        )
        downloader.download(query=url)
        showinfo("Info", "Tous les fichiers téléchargés avec succès")
        self.initialise_download_textbox()

    def download_song(self, url_crypte) -> None:
        if (
            self.SPOTIFY_PLAYLIST_URI in url_crypte
            or self.SPOTIFY_TRACK_URI in url_crypte
        ):
            decrypt_word = url_crypte
        else:
            decrypt_word = SimpleEncryption(url=None)._decrypt_url(url_crypte)

        value = self.sp_client.link(decrypt_word)
        tracks = [track.url for track in value]
        self.view.textbox.insert(
            tkinter.INSERT,
            f"Downloading {len(tracks)} songs, telechargement en cours....",
        )
        self.initialise_down_entry()
        with ThreadPool() as pool:
            pool.apply_async(self.download_one_song, (decrypt_word,))
            print()

    def initialise_down_entry(self):
        try:
            self.view.down_path.set("")
            self.view.link_entry.delete(0, tkinter.END)
        except:
            raise ComponentError

    def download_songs(self, down_path: str):
        progress = 0
        start_time = time.time()

        if down_path.startswith("https"):
            tab = down_path.split("/")
            playlist_id = tab[len(tab) - 1]
        else:
            playlist_url = SimpleEncryption(url=None)._decrypt_url(down_path).split("/")
            playlist_id = playlist_url[len(playlist_url) - 1]

        try:
            value = self.sp_client._get_playlist_tracks(playlist_id=playlist_id)
            tracks = [track.url for track in value]
            self.view.textbox.insert(
                tkinter.INSERT, f"Downloading {len(tracks)} songs...\n"
            )

            with ThreadPool(cpu_count()) as pool:
                jobs = pool.map_async(self.download_one_song, tracks, chunksize=20)

                failed_jobs = []
                for job in jobs.get():
                    if job["returncode"] != 0:
                        failed_jobs.append(job)
                    else:
                        self.view.progressbar.start()
                        progress = 1 / len(tracks) + progress
                        self.view.progressbar.set(progress)
                        message = (
                            f"Download Finished!\n\tCompleted {len(tracks) - len(failed_jobs)}/{len(tracks)}"
                            f" songs in {time.time() - start_time:.0f}s\n"
                        )
                        self.view.textbox.insert(tkinter.INSERT, message)
        except Exception as error:
            raise error

    def read_file(self):
        from os import listdir

        count = 1
        try:
            for file in listdir("EkilaDownloader"):
                self.view.textbox.insert(
                    tkinter.INSERT, "\t" + str(count) + ". " + file + "\n"
                )
                count += 1
        except Exception:
            pass

    def open_song_folder(self) -> None:
        path = askdirectory(title="Selectionner un dossier")
        if self.view.convert_entry:
            self.view.convert_entry.set(str(path))
            if self.view.convert_entry.get() != "":
                self.view.son_path_entry.delete(0, tkinter.END)
            self.view.son_path_entry.insert(0, str(path))

    async def convert_mp3_to_wav(self, folder_path):
        progress = 0
        if folder_path:
            directory = os.listdir(folder_path)
            if len(directory) > 0:
                self.view.progressbar.configure(determinate_speed=1)
                speed = 1 / len(directory)
                for file in directory:
                    is_file_mp3 = Utils.is_mp3(file)
                    try:
                        if is_file_mp3:
                            self.view.progressbar.start()
                            self.view.progressbar.stop()
                            await Utils.mp3_to_wav(folder_path + "/" + file)
                            progress = speed + progress
                            self.view.progressbar.set(progress)
                    except Exception as error:
                        raise error

                self.view.progressbar.stop()
                self.view.progressbar.set(0)
                self.view.convert_entry.set("")
                showinfo("Info", "Operation terminée")
            else:
                showwarning("Warning", "Dossier vide")
        else:
            showwarning("Warning", "Choisir un dossier")

    async def _write_metadata_in_xls_file(self, song_path: str, album: str) -> None:
        if song_path and song_path.endswith(".mp3"):
            data_meta = self.get_all_data(song_path, self.num_track, album)
            metas, contribs = self.get_data(data_meta)
            self.view.son_path_entry.delete(0, tkinter.END)
            self.excel_handler.write_in_xlsx_file(
                data=(metas, contribs),
                meta_start=self.meta_start,
                contrib_start=self.contrib_start,
            )
            self.len_meta = len(metas)
            self.len_contrib = len(contribs)

    def get_data(self, datas) -> Tuple[list, list]:
        """get data"""
        metas: list = []
        contribs: list = []
        for data in datas:
            meta, contrib = self.excel_handler.get_metadata(
                metadata=XlsMeta(song_metada=data)
            )
            metas.append(meta)
            contribs.append(contrib)
        return metas, contribs

    def get_all_data(self, song_path, num, album):
        all_songs = song_path.split(";")
        meta_data = []
        for _song_path in all_songs:
            data = self.excel_handler.get_file_metadata(_song_path)
            data.num_track = num
            data.album = album
            data.contributor.track = str(1) + "."
            data.contributor.set_track(num)
            num += 1
            meta_data.append(data)
        return meta_data

    async def write_many_metadata_in_xls_file(self, song_path: str) -> None:
        album: str = self.open_input_dialog_for_volume_number()
        await self._write_metadata_in_xls_file(song_path, album)
        self.excel_handler.save_file()
        self.num_track = 1
        self.meta_start += self.len_meta
        self.contrib_start += self.len_contrib
        showinfo("Info", "Operation terminée")
