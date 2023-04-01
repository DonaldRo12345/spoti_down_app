
from multiprocessing.pool import ThreadPool
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import askdirectory
from tkinter.filedialog import askopenfilenames
from crypto import SimpleEncryption
from spotify import SpotifyCustomer
from tkinter.messagebox import askyesno, showwarning
from tkinter.messagebox import showinfo
from exceptions import SongError
from exceptions import ComponentError
from utils import Utils
from downloader import Downloader
from type import Quality, Format
from utils import PathHolder
from pathlib import Path

import csv
import tkinter
import customtkinter
import asyncio
import os


class Controller:

    SPOTIFY_PLAYLIST_URI = 'https://open.spotify.com/playlist/'
    SPOTIFY_TRACK_URI = 'https://open.spotify.com/track/'

    def __init__(self, view, sp_client:SpotifyCustomer):
        self.view = view
        self.sp_client = sp_client
        self.state = {
            'search_songs': []
        }
        self.search_songs = []
    
    def create_playlist(self, playlist_name):
        """ permit a user to create a playlist"""

        return self.sp_client.create_playlists(playlist_name)

    def delete_playlist(self, playlist_id):
        """ permit a user to delete a playlist"""

        try:
            if playlist_id:
                entry = askyesno(
                    title='Suppression', 
                    message='Voulez vous supprimer cette playlist ?'
                )
                if entry:
                    self.sp_client.delete_playlist(playlist_id)
                    self.sp_client.get_playlist_from_api()
                    asyncio.run(self.checkbox_playlist_output())
            else:
                showwarning('Warning', 'Choisir une playlist')
        except Exception as error:
            raise error

    def delete_cache(self):
        """ delete cache file and actualise app """
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
        """ get playlist to catch update made """

        try:
            self.sp_client.get_playlist_from_api()
        except Exception as error:
            raise error
        return
    
    def open_file(self):
        """ get csv file path """

        filetypes = (('csv files', '*.csv'), ('All files', '*.csv'))
        file_path = askopenfilename(
            title='ouvrir un fichier', 
            filetypes=filetypes
        )
        return file_path
        
    def open_file_mp3(self):
        """ get mp3 file path """

        filetypes = (('mp3 files', '*.mp3'), ('All songs files', '*.mp3'))
        file_mp3_path = askopenfilename(
            title='ouvrir un fichier audio', 
            filetypes=filetypes
        )
        return file_mp3_path

    async def read_sng(self, query: str):
        """search a song on spotify and return song link """

        spotify_link, artist_name, song_title = self.sp_client.search_song(query)
        if query is None or spotify_link is None:
            pass
        else:
            self.search_songs.append({
                'song_link': spotify_link,
                'artist': artist_name,
                'title': song_title
            })
        return spotify_link
    
    async def read_unique_file(self, file_path):
        """read song on csv file and print response on screen """

        song_title, count = [], 0
        self.search_songs = []
        progress = 0
        if file_path:
            with open(file_path, mode='r', encoding="utf8", errors='ignore') as file:
                csvreader = csv.reader(file)
                for row in csvreader:
                    new_row = row[0].split(";")
                    if new_row[1] != 'Listen num':
                        song_title.append(new_row[1])

            self.view.progressbar.configure(determinate_speed=1)
            for song in song_title:
                try:
                    await self.read_sng(song)
                    if self.view.textbox_csv:
                        self.view.textbox_csv.insert(tkinter.INSERT, '\t' + str(count) + '. ' + song + '\n')
                        self.view.update()
                        self.view.progressbar.start()
                        progress = 1 / len(song_title) + progress
                        self.view.progressbar.set(progress)
                        count += 1
                except Exception:
                    raise SongError
            self.view.progressbar.stop()
            showinfo('Success', f'Opération terminée')
            self.initialise_entry()
        else:
            showwarning('message', 'Veuillez choisir un fichier!')

    def initialise_entry(self):
        """ initialise csv entries """

        try:
            self.view.file_path.set('')
            self.view.csv_entry.delete(0, tkinter.END)
            self.view.textbox_csv.delete("0.0", "end")
            self.view.progressbar.set(0)
        except:
            raise ComponentError

    async def song_panel(self):
        """ print all song extract from csv in transfert song panel """

        try:
            self.check_var = tkinter.StringVar()
            self.header = customtkinter.CTkCheckBox(
                self.view.scrollable_sons_frame, 
                text="Headers",
                variable=self.check_var,
                command=self.select_checkboxes,
                onvalue="on", 
                offvalue="off"
            )
            self.header.grid(row=0, column=0, pady=(0, 10), sticky='nw')

            self.scrollable_frame_switches = []
            self.checkbox_value = tkinter.StringVar()

            for i, songs in enumerate(self.search_songs):
                await self.checkbox_song_output(songs, i)
                self.view.update()
        
        except Exception as err:
            print(err)

    async def checkbox_song_output(self, songs, index):
        try:
            checkbox = customtkinter.CTkCheckBox(
                self.view.scrollable_sons_frame, 
                text=songs['artist'] + '- ' + songs['title'],
                variable=self.checkbox_value,
                onvalue=songs['song_link'],
                offvalue='off', 
            )
            checkbox.grid(row=index+1, column=0, pady=(0, 10), sticky='nw', padx=30)
            self.scrollable_frame_switches.append(checkbox)
        except Exception as error:
            raise error

    async def select_and_deselect(self):
        self.items_selected = []
        self.current_header_state = self.check_var.get()

        if self.current_header_state == "on":
            for checkbox in self.scrollable_frame_switches:
                await Utils.select_checkbox(checkbox)
                self.items_selected.append(self.checkbox_value.get())
                self.view.update()
        elif self.current_header_state == "off":
            for checkbox in self.scrollable_frame_switches:
                await Utils.deselect_checkbox(checkbox)
                self.view.update()
    
    def select_checkboxes(self):
        asyncio.run(self.select_and_deselect())

    async def checkbox_playlist_output(self):
        """ print all user's playlist in transfert song panel """

        all_playlist = self.sp_client.get_user_plalists()
        self.playlist_var = tkinter.StringVar()
        self.scrollable_playlist_switches = []

        for idx in range(0,len(all_playlist)-1):
            await self.create_playlist_checkbox(all_playlist[idx], idx)
            self.view.update()

    async def create_playlist_checkbox(self, value, idx):
        """ create unique playlist  """

        checkbox =  customtkinter.CTkRadioButton(
            self.view.scrollable_sons_list, 
            text=value['name'].encode(encoding="ascii",errors="ignore").decode("utf-8"),
            value=value['id'],
            variable=self.playlist_var,
            command=self.selected_playlist
        )
        checkbox.grid(row=idx, column=0, pady=(0, 10), sticky='nw', padx=30)
        self.scrollable_playlist_switches.append(checkbox)
        
    def selected_playlist(self):
        print("selected playlist:: ", self.playlist_var.get())

    def get_playlist_id(self):
        return self.playlist_var.get()

    def get_selected_playlist(self):
        """ get selected playlist title """

        playlist_id = self.playlist_var.get()
        playlist_name = None
        if playlist_id:
            playlist_name = self.sp_client._get_playlist_name(playlist_id)
            return playlist_name
        return playlist_name

    def copy_link(self):
        """ copy a playlist link """

        if self.playlist_var.get():
            playlist_uri = self.SPOTIFY_PLAYLIST_URI + self.playlist_var.get()
            encrypted_link = SimpleEncryption(url=playlist_uri)._encrypt_url()
            Utils.copy_paste_text(self.view, encrypted_link)
            showinfo('Info', 'actualiser avec succès')

    async def transfert_songs(self):
        """ transfert selected songs in a playlist """

        progress = 0
        playlist_name = self.get_selected_playlist()
        try:
            if len(self.items_selected) > 0:
                if playlist_name:
                    self.view.progressbar.configure(determinate_speed=1)
                    for song in self.items_selected:
                        self.view.progressbar.start()
                        self.view.progressbar.stop()
                        await self.sp_client.send_one_song_to_playlist(
                            song_uri=song,
                            playlist_title=playlist_name
                        )
                        self.view.update()
                        progress = 1 / len(self.items_selected) + progress
                        self.view.progressbar.set(progress)
                    self.view.progressbar.stop()
                    self.view.progressbar.set(0)
                    self.copy_link()
                    showinfo('Success', f'transfert terminée, lien copié')
                    for checkbox in self.scrollable_frame_switches:
                        await Utils.deselect_checkbox(checkbox)
                        self.view.update()
                    Utils.deselect_checkbox(self.header)
                else:
                    showwarning('Warning', 'Choisir une playlist')
            else:
                showwarning('Warning', 'Choisir tous les sons')

        except Exception as error:
            raise error

    def download_one_song(self, url):
        downloader = Downloader(
            sp_client=self.sp_client,
            quality=Quality.BEST,
            download_format=Format.MP3,
            path_holder=PathHolder(downloads_path=os.getcwd() + '/EkilaDownloader')
        )
        downloader.download(query=url)

    def initialise_down_entry(self):
        try:
            self.view.down_path.set('')
            self.view.link_entry.delete(0, tkinter.END)
        except:
            raise ComponentError

    def download_songs(self, down_path):
        if down_path != '':
            decrypt_word = SimpleEncryption(url=None)._decrypt_url(down_path)
            try:
                with ThreadPool() as pool:
                    self.initialise_down_entry()
                    pool.apply_async(self.call_download_function, (decrypt_word,))
                    self.read_file()
            except Exception as error:
                raise error
        else:
            showwarning('Warning', "Copier le lien d'une playlist")

    def call_download_function(self, link_crypt):
        downloader = Downloader(
            sp_client=self.sp_client,
            quality=Quality.BEST,
            download_format=Format.MP3,
            path_holder=PathHolder(downloads_path=os.getcwd() + '/EkilaDownloader')
        )
        downloader.call_download(link_crypt)
        showinfo('Info', 'Tous les fichiers téléchargés avec succès')
        self.view.textbox.delete("0.0", "end")

    def read_file(self):
        from os import listdir
        count = 1
        for file in listdir('EkilaDownloader'):
            self.view.textbox.insert(tkinter.INSERT, '\t' + str(count) + '. ' + file + '\n')
            count += 1

    def open_song_folder(self):
        path = askdirectory(title='Selectionner un dossier')
        if self.view.convert_entry:
            self.view.convert_entry.set(str(path))
            if self.view.convert_entry.get() != '':
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
                            await Utils.mp3_to_wav(folder_path + '/' + file)
                            progress = speed + progress
                            self.view.progressbar.set(progress)
                    except:
                        pass
                    
                self.view.progressbar.stop()
                self.view.progressbar.set(0)
                self.view.convert_entry.set('')
                showinfo('Info', 'Operation terminée')
            else: showwarning('Warning', 'Dossier vide')
        else: showwarning('Warning', 'Choisir un dossier')

    



       
        

        

 

    

    



        
    
 