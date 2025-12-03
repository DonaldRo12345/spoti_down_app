# coding:utf-8
import asyncio
import csv
import logging
import os
import tkinter
from tkinter import *
from tkinter import simpledialog, tix, ttk
from tkinter.filedialog import *
from tkinter.filedialog import askdirectory, askopenfilename, askopenfilenames
from tkinter.messagebox import *
from tkinter.messagebox import showerror, showinfo, showwarning
from tkinter.scrolledtext import *

import eyed3
import music_tag
import requests.exceptions as internetException
from pydub import AudioSegment

from crypto import SimpleEncryption
from exceptions import SpotifyCustomerException
from settings import settings
from spotify import APIConfig, SpotifyCustomer
from utils import copy_csv_to_another

__all__ = ["SpotifyCustomerException"]


class ApplicationInterface:

    """
    this file permit us to generate
    a GUI for user to enter information.
    """

    logging.basicConfig(
        format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
        filename="error.log",
        level=logging.DEBUG,
        datefmt="%m/%d/%Y %I:%M:%S %p",
    )
    SPOTIFY_TRACK_URI = "https://open.spotify.com/track/"
    SPOTIFY_PLAYLIST_URI = "https://open.spotify.com/playlist/"

    global logger
    logger = logging.getLogger(__name__)

    conf = APIConfig
    conf.SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
    conf.USER_ID = os.environ.get("USER_ID")
    conf.SPOTIPY_REDIRECT_URI = os.environ.get("SPOTIPY_REDIRECT_URI")
    conf.SPOTIFY_CLIENT_SECRET_KEY = os.environ.get("SPOTIFY_CLIENT_SECRET_KEY")
    conf.scopes = settings.SCOPES

    def __init__(self, master):
        self.file = None
        self.file_mp3 = None
        self.master = master
        self.search_songs = []
        self.playlist_name = None
        self.uri = None
        self.is_finish = False
        self.number_playlist = 0
        self.selected_songs = set()
        self.playlist_id = None
        self.playlist_title = None
        self.song_not_found = []
        self.spotify_client = SpotifyCustomer(config=self.conf)
        self.master.title("Ekila Downloader")
        self.master.iconbitmap("images/logo.ico")
        self.master.resizable(width=False, height=False)

        # setup toolbar----------------------------------------------------
        menu_bar = Menu(self.master)

        self.master.config(menu=menu_bar)

        menu_file = Menu(menu_bar, tearoff=0)
        menu_help = Menu(menu_bar, tearoff=0)

        menu_bar.add_cascade(label="Fichier", menu=menu_file)
        menu_bar.add_cascade(label="Aide", menu=menu_help)

        menu_file.add_cascade(label="Ouvrir un fichier csv", command=self.open_file)
        menu_file.add_cascade(
            label="Ouvrir un fichier audio", command=self.open_file_mp3
        )
        menu_file.add_cascade(
            label="Ouvrir un dossier contenant les sons", command=self.open_song_folder
        )
        menu_file.add_separator()
        menu_file.add_cascade(
            label="Créer une playlist ekila", command=self.create_playlists
        )
        menu_file.add_cascade(
            label="Copier le lien de la playlist",
            command=self.get_selected_playlist_link,
        )
        menu_file.add_cascade(
            label="Supprimer une playlist", command=self.delete_playlist
        )
        # menu_file.add_separator()
        menu_file.add_cascade(label="Vider", command=self.clear_all)
        menu_file.add_separator()
        menu_file.add_cascade(label="Quitter", command=self.quit)
        menu_help.add_command(label="A propos", command=self.about)

        # setup bar navigation----------------------------------------------
        note = ttk.Notebook(self.master, width=900, height=400)
        note.grid_rowconfigure(0, weight=1)
        note.grid_columnconfigure(0, weight=1)
        note.grid(row=0, pady=10)

        self.page_one = ttk.Frame(note)
        self.page_one.grid(row=0, column=0)

        self.page_two = ttk.Frame(note)
        self.page_two.grid(row=0, column=0)

        self.page_tree = ttk.Frame(note)
        self.page_tree.grid(row=0, column=0)

        self.page_four = ttk.Frame(note)
        self.page_four.grid(row=0, column=0)

        note.add(self.page_one, text="Ekila stream")
        note.add(self.page_two, text="Insertion des sons")
        note.add(self.page_tree, text="Conversions wav et modification")
        note.add(self.page_four, text="Téléchargement des sons")

        # setup widget 😀 ----------------------------------------------------

        # Label(self.page_one, text='Welcome to your spotify extrator', font='Helvetica 12 bold').grid(
        #     row=3, columnspan=3, pady=10, padx=15)

        # ---------------------- first window -------------------------------------
        self.file_path = StringVar()
        Label(self.page_one, text="Fichier CSV:", font="Helvetica 10 bold").grid(
            row=4, columnspan=3, pady=10, padx=15
        )
        self.entry = Entry(
            self.page_one, width=60, state="readonly", textvariable=self.file_path
        )
        self.entry.grid(row=4, column=3, pady=10, ipady=6)

        Label(self.page_one, text="Liste des sons:", font="Helvetica 10 bold").grid(
            row=5, columnspan=3, pady=10, padx=15
        )

        self.text = ScrolledText(
            self.page_one, height=10, width=80, pady=2, padx=3, undo=True
        )
        self.text.grid(row=5, column=3, pady=10, ipady=6)
        self.text.configure(bg="#c8d3e6")
        Button(
            self.page_one,
            text="Generer",
            width=10,
            bg="green",
            command=self.generate_link,
        ).grid(row=6, column=1, padx=1, pady=10, ipady=6)

        # ---------------------- second window -------------------------------------
        self.song_path = StringVar()
        Label(self.page_tree, text="Fichier mp3:", font="Helvetica 10 bold").grid(
            row=4, column=0, columnspan=3, pady=10, padx=10
        )
        self.entry_song_path = Entry(
            self.page_tree, width=60, state="readonly", textvariable=self.song_path
        )
        self.entry_song_path.grid(row=4, column=3, pady=10, ipady=6)

        Label(self.page_tree, text="Resultat:", font="Helvetica 10 bold").grid(
            row=5, column=0, columnspan=3, pady=10, padx=10
        )
        self.song_rename = ScrolledText(self.page_tree, height=10, width=80, undo=True)
        self.song_rename.grid(row=5, column=3, pady=5)
        self.song_rename.configure(bg="#c8d3e6")
        # Button(self.page_tree, text="Renommer", width=10, bg='red',
        #        command=self.rename_audio_file).grid(row=6, column=1, padx=10, pady=10, ipady=6)
        Button(
            self.page_tree,
            text="Modifier métadata",
            width=15,
            bg="green",
            command=self.modify_metadata,
        ).grid(row=6, column=2, pady=3, padx=2)
        Button(
            self.page_tree,
            text="Convertir en wav",
            width=15,
            bg="white",
            fg="black",
            command=self.run_song_convert,
        ).grid(row=6, column=3, pady=3, padx=0)

        # ---------------------- third window -------------------------------------

        self.frame = Frame(self.page_two)
        self.frame.grid(row=0, column=0, columnspan=5, padx=5, pady=10)

        self.btn_frame = Frame(self.page_two)
        self.btn_frame.grid(row=4, column=0, padx=5)

        self.frame_playlist = Frame(self.page_two)
        self.frame_playlist.grid(row=0, column=8, columnspan=5, padx=50, pady=10)

        self.playlist_panel()
        self.songs_panel([])

        Button(
            self.btn_frame,
            text="Transférer",
            width=15,
            bg="green",
            command=self.add_song_in_playlist,
        ).grid(row=1, column=0)
        Button(
            self.btn_frame,
            text="Supprimer",
            width=15,
            bg="red",
            command=self.delete_item,
        ).grid(row=1, column=3, padx=5)

        # ---------------------- fourth window -------------------------------------
        self.sp_link = StringVar()
        Label(self.page_four, text="Lien playlist:", font="Helvetica 10 bold").grid(
            row=4, columnspan=3, pady=10, padx=15
        )
        self.entry_sp_link = Entry(self.page_four, width=60, textvariable=self.sp_link)
        self.entry_sp_link.grid(row=4, column=3, pady=10, ipady=6)

        Label(self.page_four, text="Liste des sons:", font="Helvetica 10 bold").grid(
            row=5, columnspan=3, pady=10, padx=15
        )

        self.song_download = ScrolledText(
            self.page_four, height=10, width=80, pady=2, padx=3, undo=True
        )
        self.song_download.grid(row=5, column=3, pady=10, ipady=6)
        self.song_download.configure(bg="#c8d3e6")
        Button(
            self.page_four,
            text="Télécharger",
            width=10,
            bg="green",
            command=self.download_song,
        ).grid(row=6, column=1, padx=1, pady=10, ipady=6)

    def copy_paste_text(self, text: str):
        self.master.clipboard_clear()
        self.master.clipboard_append(text)

    def get_playlist_name_uri(self, id: str, songs: list):
        name, uri = None, None
        for value in songs:
            if value["id"] == id:
                name, uri = value["name"], value["uri"]
                break
        return name, uri

    def select_child(self, item):
        if item.startswith("CL2"):
            children = self.cl2.hlist.info_children(item)
            status = self.cl2.getstatus(item)
            for child in children:
                self.cl2.setstatus(child, status)

        if item.startswith("CL1"):
            children = self.cl.hlist.info_children(item)
            status = self.cl.getstatus(item)
            for child in children:
                self.cl.setstatus(child, status)

    def select_children(self, item):
        if item.startswith("CL2"):
            children = self.cl2.hlist.info_children(item)
            status = self.cl2.getstatus(item)

            for child in children:
                self.cl2.setstatus(child, status)
                grand_child = self.cl2.hlist.info_children(child)
                while grand_child:
                    for x in grand_child:
                        self.cl2.setstatus(x, status)
                        grand_child = self.cl2.hlist.info_children(x)

    def deselect_items(self):
        for item in self.cl.getselection("on"):
            self.cl.setstatus(item, "off")
        for item in self.cl2.getselection("on"):
            self.cl2.setstatus(item, "off")

    def delete_playlist(self):
        self.get_selected_playlist()
        try:
            if self.playlist_id is not None:
                entry = askyesno(
                    title="Suppression", message="Voulez vous supprimer cette playlist?"
                )
                if entry:
                    self.spotify_client.delete_playlist(self.playlist_id)
                    self.cl2.hlist.delete_entry("CL2." + self.playlist_id)
                    self.master.update()
        except Exception as error:
            logger.error(error)
            showerror("Error", error)

    def get_selected_songs(self):
        for item in self.cl.getselection("on"):
            if item.startswith("CL1."):
                self.selected_songs.add(self.SPOTIFY_TRACK_URI + item.split(".")[1])

    def get_selected_playlist_link(self):
        self.get_selected_playlist()
        if self.playlist_id is not None:
            playlist_uri = self.SPOTIFY_PLAYLIST_URI + self.playlist_id
            encrypted_link = SimpleEncryption(url=playlist_uri)._encrypt_url()
            self.copy_paste_text(encrypted_link)
            showinfo("Info", "Lien copié crypté")
        else:
            showwarning("Warning", "sélectionner une seule playlist")

    def get_selected_playlist(self):
        info = self.cl2.hlist.info_selection()
        self.playlist_id = None

        if len(info) == 0:
            showwarning("Warning", "aucune playlist sélectionné")

        if len(info) == 1:
            if info[0] == "CL2":
                showwarning("Warning", "veuillez choisir une seule playlist")
            else:
                if len(info[0].split(".")) > 2:
                    showwarning("Warning", "veuillez choisir une playlist correcte")
                else:
                    self.playlist_id = info[0].split(".")[1]

        if len(info) > 1:
            showwarning("Warning", "veuillez choisir une playlist")

    def delete_item(self):
        items = self.cl.getselection("on")
        if len(items) > 0:
            for item in items:
                if item.startswith("CL1."):
                    self.cl.hlist.delete_entry(item)
                pass
            self.master.update()
        else:
            showwarning("Warning", "Aucun son sélectionné")

    def initialise_entry(self):
        self.file_path.set("")
        self.text.delete("1.0", END)

    def _read_unique_file(self, file_path):
        song_title, count = [], 0
        self.search_songs = []
        with open(file_path, mode="r", encoding="utf8", errors="ignore") as file:
            csvreader = csv.reader(file)
            for row in csvreader:
                new_row = row[0].split(";")
                if new_row[1] != "Listen num":
                    song_title.append(new_row[1])

        for song in song_title:
            try:
                response = self.read_sng(song)
                if response is not None:
                    self.text.insert(tkinter.INSERT, str(count) + ". " + song + "\n")
                    count += 1
            except Exception as error:
                print(error)

        self.cl.pack_forget()
        self.songs_panel(self.search_songs)
        self.initialise_entry()
        self.loader.grid_forget()
        showinfo("Success", f"Opération terminée")

    def make_copy_file(self, files: list):
        dest_file = files[0]
        for i in range(1, len(files)):
            copy_csv_to_another(source_file=files[i], dest_file=dest_file)
        return dest_file

    def run_async_pool(self, files: list):
        from multiprocessing.pool import ThreadPool

        if len(files) == 1:
            with ThreadPool() as pool:
                _ = pool.apply_async(self._read_unique_file, (files[0],), callback=None)
                self.create_loader(self.page_one, "Recherche en cours...", 8, 3)

        if len(files) >= 2:
            file = self.make_copy_file(files)
            with ThreadPool() as pool:
                _ = pool.apply_async(self._read_unique_file, (file,))
                self.create_loader(self.page_one, "Recherche en cours...", 8, 3)

    async def read_file(self):
        if len(self.files) > 0:
            self.run_async_pool(self.files)
        else:
            showwarning("Attention", "Veuillez choisir un fichier csv!")

    def seperate_url(self, url: str):
        result = url.split("/")
        return result[len(result) - 1]

    def initialise(self):
        self.selected_songs = set()
        self.playlist_name = None

    def open_file(self):
        filetypes = (("csv files", "*.csv"), ("All files", "*.csv"))
        self.file = askopenfilenames(title="ouvrir un fichier", filetypes=filetypes)
        self.files = [file for file in self.file]
        file = " ; ".join(self.file)
        self.file_path.set(str(file))
        if self.file_path.get() != "":
            self.entry.delete(0, END)
        self.entry.insert(0, str(file))

    def open_file_mp3(self):
        filetypes = (("mp3 files", "*.mp3"), ("All songs files", "*.mp3"))
        self.file_mp3 = askopenfilename(
            title="ouvrir un fichier audio", filetypes=filetypes
        )
        self.song_path.set(str(self.file_mp3))
        if self.song_path.get() != "":
            self.entry_song_path.delete(0, END)
        self.entry_song_path.insert(0, str(self.file_mp3))

    def open_song_folder(self):
        path = askdirectory(title="Selectionner un dossier")
        self.song_path.set(str(path))
        if self.song_path.get() != "":
            self.entry_song_path.delete(0, END)
        self.entry_song_path.insert(0, str(path))

    def is_mp3(self, file: str):
        return file.endswith(".mp3")

    def songs_panel(self, songs_list):
        self.cl = tix.CheckList(
            self.frame, command=self.select_child, browsecmd=self.select_child
        )
        self.cl.pack(
            fill=tkinter.BOTH, side=tkinter.LEFT, padx=5, pady=5, ipady=30, expand=1
        )
        self.cl.hlist.add("CL1", text=f"Listes des songs : {len(songs_list)} sons")
        self.cl.setstatus("CL1", "off")
        i: int = 0
        if len(songs_list) > 0:
            for obj in songs_list:
                try:
                    i += 1
                    self.cl.hlist.add(
                        "CL1." + self.seperate_url(obj["song_link"]),
                        text=f"{ i}. " + obj["artist"] + " - " + obj["title"],
                    )
                    self.cl.setstatus(
                        "CL1." + self.seperate_url(obj["song_link"]), "off"
                    )
                except:
                    pass
            self.cl.config(width=350, height=200)
            self.cl.autosetmode()

    def playlist_panel(self):
        all_playlist: list = self.spotify_client.get_user_plalists()
        self.number_playlist = len(all_playlist)
        self.cl2 = tix.CheckList(
            self.frame_playlist,
            command=self.select_children,
            browsecmd=self.select_children,
        )
        self.cl2.pack(
            fill=tkinter.BOTH, side=tkinter.LEFT, padx=15, pady=5, ipady=30, expand=1
        )
        self.cl2.hlist.add("CL2", text="Listes des playlists")
        self.cl2.setstatus("CL2", "off")
        for value in all_playlist:
            self.cl2.hlist.add("CL2." + value["id"], text=value["name"])
            self.cl2.setstatus("CL2." + value["id"], "off")
            self.cl2.autosetmode()

            songs = self.spotify_client._get_playlist_tracks(value["id"], True)
            count: int = 0
            for item in songs:
                try:
                    count += 1
                    self.cl2.hlist.add(
                        "CL2." + value["id"] + "." + item.id,
                        text=f"{count}. " + item.__str__(),
                    )
                    self.cl2.setstatus("CL2." + value["id"] + "." + item.id, "off")
                except:
                    pass

        self.cl2.config(width=400, height=200)
        self.cl2.autosetmode()

    def rename_audio_file(self):
        path = self.song_path.get()
        if path:
            if os.path.isfile(path):
                path = path.split("/")
                old_path = path[len(path) - 1]
                print(old_path)
                sng_path = old_path.split("-")
                sng_path = sng_path[0].upper() + "-" + sng_path[1]
                print(sng_path)
                del path[len(path) - 1]
                main_path = "/".join(path)
                try:
                    os.rename(main_path + "/" + old_path, main_path + "/" + sng_path)
                    self.song_rename.insert("0.0", main_path + "/" + sng_path + "\n")
                    self.entry_song_path.delete(0, END)
                    self.master.update()
                except Exception as error:
                    logger.error(error)
                    showerror("Error", error)
        else:
            showwarning("Warning", "Veuillez ouvrir un fichier audio")

    async def set_many_songs_metadata(self):
        path = self.song_path.get()
        try:
            if path:
                if path.endswith(".mp3"):
                    await self.set_song_metadata(path)
                    showinfo(
                        "info", "Données du fichier(s) audio(s) modifiées avec succès"
                    )
                else:
                    directory = os.listdir(path)
                    if len(directory) > 0:
                        for file in directory:
                            if file.endswith(".mp3"):
                                await self.set_song_metadata(path + "/" + file)
                                self.song_rename.insert("0.0", path + "/" + file + "\n")
                                self.master.update()
                            else:
                                pass
                        showinfo(
                            "info",
                            "Données du fichier(s) audio(s) modifiées avec succès",
                        )
                    else:
                        showerror("Error", "dossier vide")
                self.song_path.set("")
            else:
                showwarning(
                    "Attention", "Veuillez choisir un fichier audio ou un dossier!"
                )
        except Exception as error:
            print(error)
            showerror("Error", error)

    async def set_song_metadata(self, path: str):
        if path:
            try:
                audio = music_tag.load_file(path)
                audiofile = eyed3.load(path)
                if audio["artist"] is not None and audio["albumartist"] is not None:
                    print(audio)
                    audio["artist"] = audiofile.tag.artist.upper()
                    audio["albumartist"] = audiofile.tag.artist.upper()
                    audio["isrc"] = ""
                    audio.save()
            except Exception as err:
                logger.error(err)

    def read_sng(self, query: str):
        spotify_link, artist_name, song_title = self.spotify_client.search_song(query)
        self.song_not_found: list = []
        if query is None or spotify_link is None:
            pass
        else:
            self.search_songs.append(
                {"song_link": spotify_link, "artist": artist_name, "title": song_title}
            )
        return spotify_link

    async def mp3_to_wav(self, file: str):
        sound = AudioSegment.from_mp3(file)
        path = file.split("/")
        filename = path[len(path) - 1].split(".")[0]
        del path[len(path) - 1]
        path = "/".join(path) + "/"

        try:
            if os.path.isdir(path + "fichier-wav"):
                sound.export(
                    path + "fichier-wav" + "/" + filename + ".wav", format="wav"
                )
                print("done in exists")
            else:
                os.mkdir(path + "fichier-wav")
                sound.export(
                    path + "fichier-wav" + "/" + filename + ".wav", format="wav"
                )
                print("done in not exist")
        except Exception as error:
            logger.error(error)

    def create_loader(self, frame, text, row, column):
        self.loader = Label(frame, text=text, font="Helvetica 12 bold")
        self.loader.grid(row=row, column=column, pady=5)

    def gif_loader(self, frame, row, column):
        try:
            image = PhotoImage(file="images/load.gif", format="gif -index 2")
            self.loader = Label(frame, image=image)
            self.loader.grid(row=row, column=column, pady=5)
            self.master.update()
        except Exception as error:
            pass

    async def convert_mp3_to_wav(self):
        path = self.song_path.get()
        try:
            if path:
                if path.endswith(".mp3"):
                    showwarning(
                        "Warning",
                        "Veuillez choisir un dossier contenant des fichiers mp3 svp",
                    )
                else:
                    directory = os.listdir(path)
                    if len(directory) > 0:
                        self.create_loader(
                            self.page_tree, "Conversion en cours...", 8, 3
                        )
                        for file in directory:
                            is_file_mp3 = self.is_mp3(file)
                            if is_file_mp3:
                                await self.mp3_to_wav(path + "/" + file)
                            else:
                                pass
                        self.loader.grid_forget()
                        self.master.update()
                        showinfo("Info", "Tous les fichiers convertis avec succès")
                    else:
                        showerror("Error", "Dossier vide")
                self.song_path.set("")
            else:
                showwarning("Attention", "Veuillez choisir un dossier de fichier mp3!")
        except Exception as error:
            logger.error(error)
            showerror("Error", error)

    def create_playlists(self):
        answer = simpledialog.askstring(
            "Titre de la playlist", "Entrer le titre de la playlist", parent=self.master
        )
        if answer is not None:
            try:
                is_create = self.spotify_client.create_playlists(answer)
                if not is_create:
                    showinfo("Info", "playlist créee avec succès")
                else:
                    showwarning(
                        "Attention", "la playlist {} existe déjà".format(answer)
                    )
                self.cl2.pack_forget()
                self.playlist_panel()
            except Exception as error:
                logger.error("Error", error)

    def check_song_exist_in_playlist(self, song_uri: str):
        return (
            self.spotify_client.is_song_exist(self.playlist_title, song_uri),
            song_uri,
        )

    def send_song_to_playlist(self, song_uri: str):
        tab_song = []
        tab_song.append(song_uri)
        try:
            if self.playlist_title is not None:
                self.spotify_client.add_items_in_playlist(
                    playlist_name=self.playlist_title, tracks=tab_song
                )
        except Exception as error:
            showerror("error", error)

    def minify_link(self, list_links: list):
        return ";".join(list_links)

    def _send_song_to_playlist(self, uri: str):
        tab_links = uri.split(";")
        for link in tab_links:
            self.send_song_to_playlist(link)
        self.loader.grid_forget()
        self.master.update()
        playlist_uri = self.SPOTIFY_PLAYLIST_URI + self.playlist_id
        encrypted_link = SimpleEncryption(url=playlist_uri)._encrypt_url()
        self.copy_paste_text(encrypted_link)
        self.initialise()
        self.deselect_items()
        showinfo(
            "Info",
            f"sons ajoutés à la playlist {self.playlist_title} avec succès, lien de la playlist copié",
        )

    def update_playlist_panel(self, uri: str):
        song_id = self.seperate_url(uri)
        song_label = self.cl.hlist.item_cget("CL1." + song_id, 0, "-text").split(".")[1]
        try:
            if self.playlist_id is not None:
                self.cl2.hlist.add(
                    "CL2." + self.playlist_id + "." + song_id, text=song_label
                )
                self.cl2.setstatus("CL2." + self.playlist_id + "." + song_id, "off")
                self.master.update()
        except:
            pass

    """
        Transfert selected songs in a playlist
        if that song didn't already exist in the playlist
    """

    async def add_track_in_playlist(self):
        from multiprocessing import cpu_count
        from multiprocessing.pool import ThreadPool

        song_to_send = []
        self.get_selected_songs()
        self.get_selected_playlist()

        if self.playlist_id is not None:
            playlist_title = self.spotify_client._get_playlist_name(self.playlist_id)
            self.playlist_title = playlist_title

            try:
                if playlist_title is not None and len(list(self.selected_songs)) >= 1:
                    with ThreadPool(cpu_count()) as pool:
                        jobs = pool.map_async(
                            self.check_song_exist_in_playlist, self.selected_songs
                        )
                        for job in jobs.get():
                            if not job[0]:
                                song_to_send.append(job[1])

                    if len(song_to_send) == 0:
                        showwarning(
                            "Warning",
                            f"un ou plusieurs sons sélectionnés existent déjà dans la playlist, veuillez reselectionner",
                        )
                    elif len(song_to_send) > 0:
                        try:
                            with ThreadPool(cpu_count()) as pool:
                                self.create_loader(
                                    self.btn_frame, "Transfert en cours...", 2, 3
                                )
                                if len(song_to_send) == 1:
                                    pool.apply(
                                        self.send_song_to_playlist, (song_to_send[0],)
                                    )
                                    self.loader.grid_forget()
                                    self.master.update()
                                    playlist_uri = (
                                        self.SPOTIFY_PLAYLIST_URI + self.playlist_id
                                    )
                                    encrypted_link = SimpleEncryption(
                                        url=playlist_uri
                                    )._encrypt_url()
                                    self.copy_paste_text(encrypted_link)
                                    showinfo(
                                        "Info",
                                        f"sons ajoutés à la playlist {self.playlist_title} avec succès, lien de la playlist copié",
                                    )
                                    self.initialise()
                                    self.deselect_items()

                                elif len(song_to_send) >= 1:
                                    unify_link = self.minify_link(song_to_send)
                                    pool.apply_async(
                                        self._send_song_to_playlist, (unify_link,)
                                    )

                                for value in song_to_send:
                                    self.update_playlist_panel(value)

                        except Exception as error:
                            showerror("Error", error)
                            self.deselect_items()
                            self.loader.grid_forget()
                        self.selected_songs = set()
                    else:
                        self.loader.grid_forget()
                        self.master.update()
                        showwarning(
                            "Warning",
                            f"un ou plusieurs sons sélectionnés existent déjà dans la playlist {playlist_title}",
                        )
                else:
                    showerror(
                        "Error",
                        "Veuillez selectionner au moins une playlist et au moins un son",
                    )

            except Exception as error:
                logger.error(error)

    def download_song(self) -> None:
        from multiprocessing.pool import ThreadPool

        decrypt_word = SimpleEncryption(url=None)._decrypt_url(self.sp_link.get())
        self.sp_link.set("")

        try:
            with ThreadPool() as pool:
                self.create_loader(self.page_four, "Téléchargement en cours...", 8, 3)
                pool.apply_async(self.call_download_function, (decrypt_word,))
                print()
        except Exception as error:
            showerror(error)
            logger.error(error)

    def call_download_function(self, link_crypt):
        from downloader import Downloader
        from type import Format, Quality
        from utils import PathHolder

        downloader = Downloader(
            sp_client=SpotifyCustomer(),
            quality=Quality.BEST,
            download_format=Format.MP3,
            path_holder=PathHolder(downloads_path=os.getcwd() + "/EkilaDownloader"),
        )
        downloader.call_download(link_crypt)
        showinfo("Info", "Tous les fichiers téléchargés avec succès")
        if self.loader:
            self.loader.grid_forget()
            self.master.update()

    def insert_metadata_in_excel(self, file_path: str):
        pass

    def add_song_in_playlist(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.add_track_in_playlist())

    async def run_song_convert(self):
        asyncio.run(self.convert_mp3_to_wav())

    def generate_link(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.read_file())

    def modify_metadata(self):
        asyncio.run(self.set_many_songs_metadata())

    def clear_all(self):
        self.file_path.set("")
        # self.song_path.set('')
        self.text.delete("0.0", END)

    def get_info_entry(self):
        return self.entry.index("0.0")

    def quit(self):
        entry = askyesno(title="Exit", message="Etes vous sur de vouloir quitter?")
        if entry:
            self.master.destroy()

    def about(self):
        showinfo(
            title="A propos",
            message="Ekila Downloader v0.1, copyright MNLV Africa \n Droits réservés",
        )


# ----------setup application--------------------
if __name__ == "__main__":
    try:
        app = tix.Tk()
        gui = ApplicationInterface(app)
        app.mainloop()
    except internetException.ConnectionError as err:
        showerror(
            "Erreur",
            "mauvaise connexion \n Vérifier votre connexion internet puis relancer",
        )
