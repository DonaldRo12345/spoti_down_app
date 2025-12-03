import os
import re
from os import environ
from pathlib import Path
from shutil import rmtree
from shutil import which
from sys import platform
from urllib.request import urlretrieve
from uuid import uuid1

import customtkinter
from pydub import AudioSegment


def clean(path) -> None:
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def create_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def check_ffmpeg() -> bool:
    return which('ffmpeg') is not None


def check_env() -> bool:
    return "SPOTIPY_CLIENT_ID" in environ and "SPOTIPY_CLIENT_SECRET" in environ


def check_file(path: Path) -> bool:
    return path.is_file()


def safe_path_string(string: str) -> str:
    keep_characters = " !£$%^&()_-+=,.;'@#~[]{}"
    new_string = ""

    for c in string:
        if c.isalnum() or c in keep_characters:
            new_string = new_string + c
        else:
            new_string = new_string + "_"

    return re.sub(r'\.+$', '', new_string.rstrip()).encode('utf8').decode('utf8')


def copy_csv_to_another(source_file, dest_file):
    import csv
    with open(source_file, mode='r', encoding="utf8", errors='ignore') as file_src, \
        open(dest_file, mode='a', encoding="utf8", errors='ignore', newline='') as file_dest:
        csvreader = csv.reader(file_src)
        csvwriter = csv.writer(file_dest)
        for row in csvreader:
            if 'Listen num' in row[0]:
                pass
            else:
                csvwriter.writerow(row)

def make_copy_file(files: list):
    dest_file = files[0]
    for i in range(1, len(files)):
        copy_csv_to_another(source_file=files[i], dest_file=dest_file)
    return dest_file

#to do Buid a function wrapper
# def iter_an_action(*args, func:function) -> None:
#     for value in args:
#         func(value)


class PathHolder:

    def __init__(self, data_path: str = None, downloads_path: str = None):
        # Setup home/data path
        if data_path is None:
            home = Path.home()

            if platform == "win32":
                self.data_path = home / 'AppData/Roaming/EkilaDownloader'

            elif platform == "linux":
                self.data_path = home / '.local/share/EkilaDownloader'

            elif platform == "darwin":
                self.data_path = home / '.local/share/EkilaDownloader'

        else:
            self.data_path = Path(data_path)

        # Setup temp path
        self.temp_path = self.data_path / "temp"
        create_dir(self.temp_path)

        # Setup downloads path
        if downloads_path is None:
            self.downloads_path = self.data_path / "downloads"
        else:
            self.downloads_path = Path(downloads_path)

        create_dir(self.downloads_path)

    def get_download_directory(self) -> Path:
        return self.downloads_path

    def get_temp_dir(self) -> Path:
        return self.temp_path

    async def download_file(self, url: str, extension: str = None) -> Path:
        file_path = self.get_temp_dir() / str(uuid1())
        if extension is not None:
            file_path = file_path.with_suffix(f'.{extension}')

        urlretrieve(url, str(file_path))
        return file_path


class Utils:

    @staticmethod
    def seperate_url(url: str):
        result = url.split('/')
        return result[len(result)-1]

    @staticmethod
    def make_copy_file(files: list):
        dest_file = files[0]
        for i in range(1, len(files)):
            copy_csv_to_another(source_file=files[i], dest_file=dest_file)
        return dest_file

    @staticmethod
    def is_mp3(file: str):
        return file.endswith('.mp3')

    @staticmethod
    async def deselect_checkbox(checkbox:customtkinter.CTkCheckBox):
        """ select one checkbox of list of songs """
        checkbox.deselect()

    @staticmethod
    async def select_checkbox(checkbox:customtkinter.CTkCheckBox):
        """ deselect one checkbox of list of songs """
        checkbox.select()

    @staticmethod
    def copy_paste_text(view, text: str):
        view.clipboard_clear()
        view.clipboard_append(text)

    @staticmethod
    async def mp3_to_wav(file: str):
        """ convert a mp3 song to wav  """

        sound = AudioSegment.from_mp3(file)
        path = file.split('/')
        filename = path[len(path)-1].split('.')[0]
        del path[len(path)-1]
        path = '/'.join(path) + '/'

        try:
            if os.path.isdir(path + 'fichier-wav'):
                sound.export(
                    path + 'fichier-wav' + '/' + filename + '.wav',
                    format='wav'
                )
            else:
                os.mkdir(path + 'fichier-wav')
                sound.export(
                    path + 'fichier-wav' + '/' + filename + '.wav',
                    format='wav'
                )
        except Exception as error:
            raise error

    @staticmethod
    def print_day(num:int) -> str:
        if num == 1:
            day = "lundi"
        elif num == 2:
            day = "mardi"
        elif num == 3:
            day = "mercredi"
        elif num == 4:
            day = "jeudi"
        elif num == 5:
            day = "vendredi"
        elif num == 6:
            day = "samedi"
        elif num == 7:
            day = "dimanche"
        return day

    @staticmethod
    def print_month(num:int) -> str:
        months = [
            "Janvier",
            "Février",
            "Mars",
            "Avril",
            "Mai",
            "Juin"
            "Juillet",
            "Aout",
            "Septembre",
            "Octobre",
            "Novembre",
            "Décembre"
        ]
        try:
            return months[num-1]
        except IndexError:
            return ""
