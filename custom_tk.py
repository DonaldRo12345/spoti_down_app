import asyncio
import tkinter as tk
import tkinter.messagebox
from datetime import datetime
from multiprocessing.pool import ThreadPool
from tkinter import Menu
from tkinter.messagebox import showinfo, showwarning

import customtkinter
from PIL import Image

from controller import Controller
from settings import settings
from spotify import APIConfig, SpotifyCustomer
from utils import Utils

# Modes: "System" (standard), "Dark", "Light"
customtkinter.set_appearance_mode("System")
# Themes: "blue" (standard), "green", "dark-blue"
customtkinter.set_default_color_theme("green")


def get_api_configuration():
    """spotify api keys"""

    conf = APIConfig
    conf.SPOTIFY_CLIENT_ID = settings.SPOTIFY_CLIENT_ID
    conf.USER_ID = settings.STEEVE_USER_ID
    conf.SPOTIPY_REDIRECT_URI = settings.STEEVE_SPOTIPY_REDIRECT_URI
    conf.SPOTIFY_CLIENT_SECRET_KEY = settings.STEEVE_SPOTIFY_CLIENT_SECRET_KEY
    conf.scopes = settings.SCOPES
    return conf


def get_date():
    """format date in french format"""
    month = datetime.today().month
    day = datetime.today().day
    year = datetime.today().year

    date = f"\t\t Le {day} {Utils.print_month(month)} {year}"
    current_date = date + " " + datetime.today().strftime("%H:%M:%S")
    return current_date


class App(customtkinter.CTk):
    """main application interface"""

    GLIPH_ICON_WIDTH = 40
    GLIPH_ICON_HEIGHT = 40

    current_date = get_date()
    logo = customtkinter.CTkImage(Image.open("images/logos.png"), size=(270, 145))
    logo_welcome = customtkinter.CTkImage(
        Image.open("images/ekila-downaudio.jpg"), size=(859, 145)
    )
    pub_image = customtkinter.CTkImage(Image.open("images/phone.jpg"), size=(250, 114))

    # button logo's
    search_image = customtkinter.CTkImage(
        Image.open("images/icon/rechercher.png"),
        size=(GLIPH_ICON_WIDTH, GLIPH_ICON_HEIGHT),
    )
    transfert_image = customtkinter.CTkImage(
        Image.open("images/icon/transférer.png"),
        size=(GLIPH_ICON_WIDTH, GLIPH_ICON_HEIGHT),
    )
    download_image = customtkinter.CTkImage(
        Image.open("images/icon/télécharger.png"),
        size=(GLIPH_ICON_WIDTH, GLIPH_ICON_HEIGHT),
    )
    convert_image = customtkinter.CTkImage(
        Image.open("images/icon/convertir.png"),
        size=(GLIPH_ICON_WIDTH, GLIPH_ICON_HEIGHT),
    )
    quit_image = customtkinter.CTkImage(
        Image.open("images/icon/quitter.png"),
        size=(GLIPH_ICON_WIDTH, GLIPH_ICON_HEIGHT),
    )

    conf = get_api_configuration()
    list_file: list = []
    is_song_loading: bool = False

    def __init__(self, user_login):
        super().__init__()

        self.title("Ekila Downloader")
        self.user_login = user_login
        self.geometry(f"{1129}x{675}")
        self.resizable(0, 0)
        self.grid_rowconfigure(6, weight=2)
        self.columnconfigure(0, weight=0)

        sp_client = SpotifyCustomer(config=self.conf)
        self.controller = Controller(view=self, sp_client=sp_client)

        self.menu_bar()
        self.header()
        self.sidebar()
        self.extrat_csv_son_panel()
        self.button_list()
        self.footer()

    def change_appearance_mode_event(self, new_appearance_mode: str):
        """setup window mode contrast"""
        if new_appearance_mode == "Mode clair":
            new_appearance_mode = "Light"
        elif new_appearance_mode == "Mode sombre":
            new_appearance_mode = "Dark"
        elif new_appearance_mode == "Mode système":
            new_appearance_mode = "System"
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    def sidebar_button_event(self):
        print("sidebar_button click")

    def get_path_file(self):
        """get file path and insert in entry"""

        path, file_list = self.controller.open_many_file()
        self.list_file = file_list
        if self.csv_entry:
            if self.csv_entry.get() != "":
                self.csv_entry.delete(0, tkinter.END)
            self.csv_entry.insert(0, str(path))

    def get_song_path(self):
        """get song file path and insert in entry"""

        song_path = self.controller.open_file_mp3()
        if self.convert_entry:
            if self.convert_entry.get() != "":
                self.son_path_entry.delete(0, tkinter.END)
            self.son_path_entry.insert(0, str(song_path))

    def get_many_song_path(self):
        """get song files path and insert in entry"""

        song_path = self.controller.open_many_mp3_file()
        if self.convert_entry:
            if self.convert_entry.get() != "":
                self.son_path_entry.delete(0, tkinter.END)
            self.son_path_entry.insert(0, ";".join(song_path))

    def sidebar(self):
        """Setup side bar of the application"""

        self.sidebar_frame = customtkinter.CTkFrame(
            self, corner_radius=0, width=250, height=420
        )
        self.sidebar_frame.grid(row=2, column=0, sticky="w")
        self.tabview = customtkinter.CTkTabview(self.sidebar_frame, width=250)
        self.tabview.grid(row=2, column=0, padx=10)
        self.tabview.add("Actualités")
        self.tabview.add("Communiqués")

        self.appearance_mode_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Appearance Mode:", anchor="w"
        )
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["Mode clair", "Mode sombre", "Mode système"],
            command=self.change_appearance_mode_event,
        )
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))
        self.pub = customtkinter.CTkLabel(
            self.sidebar_frame, text="", width=250, height=110, image=self.pub_image
        )
        self.pub.grid(row=7, column=0, padx=5)

    def menu_bar(self):
        """Setup menu bar of the application"""

        menu_bar = Menu(self)
        self.config(menu=menu_bar)

        menu_file = Menu(menu_bar, tearoff=0)
        menu_help = Menu(menu_bar, tearoff=0)

        menu_bar.add_cascade(label="Fichier", menu=menu_file)
        menu_bar.add_cascade(label="Aide", menu=menu_help)

        menu_file.add_cascade(label="Ouvrir un fichier csv", command=self.get_path_file)
        # menu_file.add_cascade(label="Ouvrir un fichier audio", command=self.get_song_path)
        menu_file.add_cascade(
            label="Ouvrir vos fichiers audios", command=self.get_many_song_path
        )
        menu_file.add_cascade(
            label="Ouvrir un dossier contenant les sons",
            command=self.controller.open_song_folder,
        )
        menu_file.add_separator()
        menu_file.add_cascade(
            label="Créer une playlist", command=self.open_input_dialog_event
        )
        menu_file.add_cascade(
            label="Copier le lien de la playlist", command=self.controller.copy_link
        )
        menu_file.add_separator()
        menu_file.add_cascade(label="Vider", command=None)
        menu_file.add_cascade(label="Actualiser", command=self.controller.delete_cache)
        menu_file.add_separator()
        menu_file.add_cascade(label="Quitter", command=self.quit)
        menu_help.add_command(label="A propos", command=self.about)

    def dashboard_title(self, frame):
        """Print title on all dashboard interface"""

        self.title_dash = customtkinter.CTkLabel(
            frame,
            text="TABLEAU DE BORD",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.title_dash.grid(row=0, column=1, pady=10, sticky="news")

    def change_time(self):
        self.current_date = get_date()
        self.date_label.configure(text=self.current_date)
        self.after(200, self.change_time)

    def header(self):
        """define the header of the application"""

        self.user_label = customtkinter.CTkLabel(
            master=self, text=f"{self.user_login} est connecté"
        )
        self.user_label.grid(row=0, column=0, sticky="nw", padx=2)
        self.date_label = customtkinter.CTkLabel(master=self, text=self.current_date)
        self.date_label.grid(row=0, column=1, padx=90, sticky="e")

        self.logo_container = customtkinter.CTkFrame(self, corner_radius=0, width=1129)
        self.logo_container.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.logo_label = customtkinter.CTkLabel(
            self.logo_container, text="", height=145, image=self.logo, width=270
        )
        self.logo_label.grid(row=1, column=0)
        self.panel_logo_label = customtkinter.CTkLabel(
            self.logo_container, text="", width=859, height=145, image=self.logo_welcome
        )
        self.panel_logo_label.grid(row=1, column=2)
        self.change_time()

    def extrat_csv_son_panel(self):
        """main dashboard interface for read csv file"""

        self.dashboard_frame = customtkinter.CTkFrame(self, corner_radius=0, width=879)
        self.dashboard_frame.grid(
            row=2, column=1, rowspan=4, columnspan=2, sticky="nsew"
        )
        self.dashboard_title(self.dashboard_frame)

        self.file_path = tkinter.StringVar()
        customtkinter.CTkLabel(
            self.dashboard_frame,
            text="Fichier csv:",
            font=customtkinter.CTkFont(size=15, weight="bold"),
        ).grid(column=1, row=1, sticky="w", pady=15, padx=5)
        self.csv_entry = customtkinter.CTkEntry(
            self.dashboard_frame, width=500, textvariable=self.file_path
        )
        self.csv_entry.grid(column=1, row=1, sticky="w", pady=15, padx=100)
        self.textbox_csv = customtkinter.CTkTextbox(
            self.dashboard_frame, width=800, height=250
        )
        self.textbox_csv.grid(row=2, column=1, pady=5, sticky="nw")
        self.generate_button = customtkinter.CTkButton(
            self.dashboard_frame,
            corner_radius=2,
            fg_color=("white", "#81f542"),
            border_width=0,
            text_color=("white", "#ffffff"),
            text="Generer",
            command=lambda: asyncio.run(self.controller.run_async_pool(self.list_file)),
        )
        self.generate_button.grid(row=3, column=1, pady=5, padx=5, sticky="nw")
        self.progressbar = customtkinter.CTkProgressBar(
            self.dashboard_frame,
            height=20,
            width=350,
            progress_color=("orange", "#FFA500"),
        )
        self.progressbar.grid(row=3, column=1, padx=150, sticky="nw", pady=5)
        self.progressbar.set(0)
        # self.percentage = customtkinter.CTkLabel(self.dashboard_frame, text="1%", justify='center',
        # fg_color='transparent').grid(row=3, column=1,padx=250 , sticky='w')

    def generate_song(self, path: str):
        asyncio.run(self.controller.read_unique_file(path))

    def transfert_son_panel(self):
        """dashboard interface for transfert sons in playlist"""

        self.transfert_frame = customtkinter.CTkFrame(self, corner_radius=0, width=850)
        self.transfert_frame.grid(
            row=2, column=1, rowspan=4, columnspan=3, sticky="nsew"
        )
        self.transfert_frame.columnconfigure(0, weight=1)
        self.transfert_frame.columnconfigure(1, weight=1)
        self.dashboard_title(self.transfert_frame)

        self.scrollable_sons_frame = customtkinter.CTkScrollableFrame(
            self.transfert_frame,
            label_text="Liste des sons",
            height=250,
        )
        self.scrollable_sons_frame.grid(row=1, column=1, sticky=tk.W + tk.E, pady=15)
        self.scrollable_sons_frame.grid_columnconfigure(0, weight=1)

        self.scrollable_sons_list = customtkinter.CTkScrollableFrame(
            self.transfert_frame,
            label_text="Liste des playlists",
            height=250,
        )
        self.scrollable_sons_list.grid(row=1, column=2, pady=15, sticky=tk.W + tk.E)
        self.scrollable_sons_list.grid_columnconfigure(0, weight=1)

        self.button_frame = customtkinter.CTkFrame(
            self.transfert_frame, corner_radius=0
        )
        self.button_frame.grid(row=2, column=1, sticky="w")
        self.button_frame.columnconfigure(0, weight=1)
        self.button_frame.columnconfigure(1, weight=1)
        self.button_frame.columnconfigure(2, weight=1)

        self.transfert_button = customtkinter.CTkButton(
            self.button_frame,
            text="Transférer",
            command=lambda: asyncio.run(self.controller.transfert_songs()),
        )
        self.supprimer_button = customtkinter.CTkButton(
            self.button_frame,
            text="Supprimer",
            command=lambda: self.controller.delete_playlist(
                self.controller.get_playlist_id()
            ),
        )
        self.progressbar = customtkinter.CTkProgressBar(
            self.button_frame,
            height=30,
            width=350,
            progress_color=("orange", "#FFA500"),
        )

        self.transfert_button.grid(row=0, column=0, sticky=tk.W + tk.E)
        self.supprimer_button.grid(row=0, column=1, sticky=tk.W + tk.E, padx=3)
        self.progressbar.grid(row=0, column=2, sticky=tk.W + tk.E, padx=3)
        self.progressbar.set(0)

    def download_son_panel(self):
        """dashboard interface for download song"""

        self.down_path = tkinter.StringVar()
        self.download_frame = customtkinter.CTkFrame(self, corner_radius=0, width=850)
        self.download_frame.grid(
            row=2, column=1, rowspan=4, columnspan=3, sticky="nsew"
        )
        self.dashboard_title(self.download_frame)
        customtkinter.CTkLabel(
            self.download_frame,
            font=customtkinter.CTkFont(size=15, weight="bold"),
            text="Lien:",
        ).grid(column=1, row=1, sticky="w", pady=15, padx=5)
        self.link_entry = customtkinter.CTkEntry(
            self.download_frame, width=500, textvariable=self.down_path
        )
        self.link_entry.grid(column=1, row=1, sticky="nsew", pady=15, padx=100)
        self.textbox = customtkinter.CTkTextbox(
            self.download_frame, width=800, height=250
        )
        self.textbox.grid(row=2, column=1, pady=5, sticky="nw")
        self.download_sons_button = customtkinter.CTkButton(
            self.download_frame,
            corner_radius=15,
            fg_color=("white", "#81f542"),
            border_width=2,
            text_color=("white", "#ffffff"),
            text="Télécharger",
            command=lambda: self.controller.download_song(self.down_path.get()),
        )
        self.download_sons_button.grid(row=3, column=1, pady=5, sticky="nw")

        self.download_progressbar = customtkinter.CTkProgressBar(
            self.download_frame,
            height=30,
            width=350,
            progress_color=("orange", "#FFA500"),
        )
        self.download_progressbar.grid(row=3, column=1, padx=150, pady=5, sticky="nw")
        self.download_progressbar.set(0)

    def conversion_son_panel(self):
        """dashboard interface for convert song in wav"""

        self.conversion_frame = customtkinter.CTkFrame(self, corner_radius=0, width=850)
        self.conversion_frame.grid(
            row=2, column=1, rowspan=4, columnspan=3, sticky="nsew"
        )
        self.dashboard_title(self.conversion_frame)
        customtkinter.CTkLabel(
            self.conversion_frame,
            text="sons mp3:",
            font=customtkinter.CTkFont(size=15, weight="bold"),
        ).grid(column=1, row=1, sticky="w", pady=15, padx=5)
        self.convert_entry = tkinter.StringVar()
        self.son_path_entry = customtkinter.CTkEntry(
            self.conversion_frame, width=500, textvariable=self.convert_entry
        )
        self.son_path_entry.grid(column=1, row=1, sticky="nsew", pady=15, padx=100)
        self.textbox = customtkinter.CTkTextbox(
            self.conversion_frame, width=800, height=250
        )
        self.textbox.grid(row=2, column=1, pady=5, sticky="nw")
        self.menu_button = customtkinter.CTkFrame(
            self.conversion_frame, corner_radius=0
        )
        self.menu_button.grid(row=3, column=1, pady=5, sticky="nw")

        self.menu_button.columnconfigure(0, weight=1)
        self.menu_button.columnconfigure(1, weight=1)
        self.menu_button.columnconfigure(2, weight=1)

        self.metadata_button = customtkinter.CTkButton(
            self.menu_button,
            corner_radius=15,
            fg_color=("white", "#81f542"),
            border_width=2,
            text_color=("white", "#ffffff"),
            text="Metadata",
            command=lambda: asyncio.run(
                self.controller.write_many_metadata_in_xls_file(
                    self.convert_entry.get()
                )
            ),
        )

        self.convert_sons_button = customtkinter.CTkButton(
            self.menu_button,
            corner_radius=15,
            fg_color=("white", "#81f542"),
            border_width=2,
            text_color=("white", "#ffffff"),
            text="Convertir en wav",
            command=lambda: self.convert_mp3_to_wav(self.convert_entry.get()),
        )

        self.progressbar = customtkinter.CTkProgressBar(
            self.menu_button, height=30, width=350, progress_color=("orange", "#FFA500")
        )

        self.metadata_button.grid(row=0, column=0, sticky=tk.W + tk.E, padx=10)
        self.convert_sons_button.grid(row=0, column=1, sticky=tk.W + tk.E, padx=10)
        self.progressbar.grid(row=0, column=2, sticky=tk.W + tk.E)
        self.progressbar.set(0)

    def execute_thread(self, folder_path):
        asyncio.run(self.controller.convert_mp3_to_wav(folder_path))

    def execute_download_thread(self, link: str):
        asyncio.run(self.controller.download_songs(link))

    def download_songs(self, link: str):
        with ThreadPool() as pool:
            pool.apply_async(self.execute_download_thread, (link,))
            print()

    def convert_mp3_to_wav(self, folder_path):
        with ThreadPool() as pool:
            pool.apply_async(self.execute_thread, (folder_path,))
            print()

    def button_list(self):
        """all pagination button for application"""

        self.button_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.button_frame.grid(row=6, column=1, sticky="w")
        self.search_button = customtkinter.CTkButton(
            self.button_frame,
            corner_radius=10,
            text_color=("black", "#000000"),
            text="Recherche",
            image=self.search_image,
            fg_color=("white", "white"),
            height=60,
            font=customtkinter.CTkFont(size=12, weight="bold"),
            command=lambda: self.paginate("Recherche"),
        )

        self.transfert_button = customtkinter.CTkButton(
            self.button_frame,
            corner_radius=10,
            text_color=("black", "#000000"),
            text="Transfert",
            image=self.transfert_image,
            fg_color=("white", "white"),
            height=60,
            font=customtkinter.CTkFont(size=12, weight="bold"),
            command=lambda: self.paginate("Transfert"),
        )

        self.download_button = customtkinter.CTkButton(
            self.button_frame,
            corner_radius=10,
            text_color=("black", "#000000"),
            text="Télécharger",
            image=self.download_image,
            fg_color=("white", "white"),
            height=60,
            font=customtkinter.CTkFont(size=12, weight="bold"),
            command=lambda: self.paginate("Télécharger"),
        )

        self.convert_button = customtkinter.CTkButton(
            self.button_frame,
            corner_radius=10,
            text_color=("black", "#000000"),
            text="Conversion",
            image=self.convert_image,
            fg_color=("white", "white"),
            height=60,
            font=customtkinter.CTkFont(size=12, weight="bold"),
            command=lambda: self.paginate("Conversion"),
        )

        self.quit_button = customtkinter.CTkButton(
            self.button_frame,
            corner_radius=10,
            text_color=("black", "#000000"),
            text="Quitter",
            image=self.quit_image,
            fg_color=("white", "white"),
            height=60,
            font=customtkinter.CTkFont(size=12, weight="bold"),
            command=self.quit,
        )

        self.button_frame.columnconfigure(0, weight=1)
        self.button_frame.columnconfigure(1, weight=1)
        self.button_frame.columnconfigure(2, weight=1)
        self.button_frame.columnconfigure(3, weight=1)
        self.button_frame.columnconfigure(4, weight=1)

        self.search_button.grid(row=0, column=0, sticky=tk.W + tk.E, padx=3)
        self.transfert_button.grid(row=0, column=1, sticky=tk.W + tk.E, padx=3)
        self.download_button.grid(row=0, column=2, sticky=tk.W + tk.E, padx=3)
        self.convert_button.grid(row=0, column=3, sticky=tk.W + tk.E, padx=3)
        self.quit_button.grid(row=0, column=4, sticky=tk.W + tk.E, padx=3)

    def paginate(self, text):
        if text == "Transfert":
            self.transfert_son_panel()
            self.transfert_button.configure(fg_color=("green", "green"))
            self.search_button.configure(fg_color=("white", "white"))
            self.download_button.configure(fg_color=("white", "white"))
            self.convert_button.configure(fg_color=("white", "white"))
            with ThreadPool() as pool:
                pool.apply_async(
                    asyncio.run, (self.controller.checkbox_playlist_output(),)
                )
                asyncio.run(self.controller.song_panel())

        elif text == "Télécharger":
            self.transfert_button.configure(fg_color=("white", "white"))
            self.search_button.configure(fg_color=("white", "white"))
            self.download_button.configure(fg_color=("green", "green"))
            self.convert_button.configure(fg_color=("white", "white"))
            self.download_son_panel()

        elif text == "Conversion":
            self.search_button.configure(fg_color=("white", "white"))
            self.transfert_button.configure(fg_color=("white", "white"))
            self.download_button.configure(fg_color=("white", "white"))
            self.convert_button.configure(fg_color=("green", "green"))
            self.conversion_son_panel()

        elif text == "Recherche":
            self.search_button.configure(fg_color=("green", "green"))
            self.transfert_button.configure(fg_color=("white", "white"))
            self.download_button.configure(fg_color=("white", "white"))
            self.convert_button.configure(fg_color=("white", "white"))
            self.extrat_csv_son_panel()

    def open_input_dialog_event(self):
        self.dialog = customtkinter.CTkInputDialog(
            text="Entrer le titre de la playlist :", title="Création playlist"
        )
        value = self.dialog.get_input()
        if value:
            is_create = self.controller.create_playlist(value)
            if not is_create:
                showinfo("Info", "playlist créee avec succès")
                self.update_playlist()
            else:
                showwarning("Attention", f"la playlist {value} existe déjà")

    def update_playlist(self):
        self.controller.get_playlist_from_api()

    def aside_element(self):
        """Aside element for notification"""

        self.aside_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.aside_frame.grid(row=2, column=0, rowspan=4, padx=3)

        self.tabview = customtkinter.CTkTabview(self.aside_frame, width=250)
        self.tabview.grid(row=0, column=0, sticky="nw")
        self.tabview.add("Actualités")
        self.tabview.add("Communiqués")
        self.pub = customtkinter.CTkLabel(
            self.aside_frame, text="", image=self.pub_image
        )
        self.pub.grid(row=1, column=0, sticky="nw")

    def footer(self):
        """application footer"""

        self.footer_frame = customtkinter.CTkFrame(self)
        self.footer_frame.grid(row=9, column=1, sticky="nsew")
        self.footer_label = customtkinter.CTkLabel(
            self.footer_frame,
            text="Copyright © MNLV Africa Sarl Tous droits réservés",
            font=customtkinter.CTkFont(size=8, weight="bold"),
        )
        self.footer_label.grid(row=0, column=1, columnspan=2, sticky="e", padx=300)

    def quit(self):
        """to exit from application"""

        from tkinter.messagebox import askyesno

        entry = askyesno(title="Exit", message="Etes vous sur de vouloir quitter?")
        if entry:
            self.destroy()

    def about(self):
        """about application"""

        from tkinter.messagebox import showinfo

        showinfo(
            title="A propos",
            message="Ekila Downloader v0.1, copyright MNLV Africa \n Droits réservés",
        )


if __name__ == "__main__":
    app = App()
    app.mainloop()
