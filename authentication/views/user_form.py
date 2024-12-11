__all__ = ['user_repo', 'models']

import re
import tkinter as tk
from tkinter.messagebox import showerror, showinfo, showwarning

import customtkinter
from PIL import Image

from ..controllers.user_controller import UserController
from ..models.User import User


class AuthForm(customtkinter.CTk):

    logo = customtkinter.CTkImage(
        Image.open("images/login.png"),
        size=(200, 200),
    )


    controller = UserController()
    is_destroy = False
    user_login = None

    def __init__(self):
        super().__init__()

        self.title("Ekila Downloader App")
        self.geometry(f"{700}x{450}")
        self.resizable(0, 0)
        self.login_form()
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)

        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=0)

        self.setup_header_logo()

    def setup_header_logo(self):
        self.label = customtkinter.CTkLabel(self,  text="", height=200, image=self.logo, width=200)
        self.label.grid(row=0, column=1, sticky=tk.W+tk.E, columnspan=2)

    def validate(self, value):
        """ Validate the email entry """

        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.fullmatch(pattern, value) is None:
            return False
        return True

    def show_message(self, error, color):
        self.label_error.configure(text=error)
        self.label_error['text_color'] = color
        self.label_error['font'] = customtkinter.CTkFont(size=10, weight="bold")
        self.label_error.grid(row=5, column=1, columnspan=2, sticky=tk.W+tk.E)

    def dismount_component(self):
        try:
            self.register_button.grid_forget()
            self.login_button.grid_forget()
            self.checkbox.grid_forget()
            if self.label_error: self.label_error.grid_forget()
        except Exception as err:
            raise err

    def go_back(self):
        self.email.grid_forget()
        self.email_entry.grid_forget()
        self.username.grid_forget()
        self.username_entry.grid_forget()
        self.password_label.grid_forget()
        self.password_entry.grid_forget()
        self.register_button.grid_forget()
        self.go_back_button.grid_forget()
        self.checkbox.grid_forget()
        self.login_form()
        if self.label_error: self.label_error.grid_forget()

    def login_form(self):

        self.email = customtkinter.CTkLabel(self,  text="Email: ")
        self.email.grid(row=1, column=1, sticky=tk.W+tk.E, pady=1)

        self.email_value = tk.StringVar()
        self.email_entry = customtkinter.CTkEntry(
            self,
            width=250,
            corner_radius=2,
            textvariable=self.email_value,
        )
        self.email_entry.grid(row=1, column=2, sticky=tk.W,  pady=1)
        self.email_entry.bind(command=lambda:self.validate(self.email_value.get()))

        self.label_error = customtkinter.CTkLabel(self)

        self.pwd_label = customtkinter.CTkLabel(self,  text="Mot de passe: ")
        self.pwd_label.grid(row=2, column=1, sticky=tk.W+tk.E, pady=10)

        self.password = tk.StringVar()
        self.password_entry = customtkinter.CTkEntry(
            self,
            show="*",
            width=250,
            corner_radius=2,
            textvariable=self.password
        )
        self.password_entry.grid(row=2, column=2, sticky=tk.W, pady=10)

        self.check_var = customtkinter.StringVar()
        self.checkbox = customtkinter.CTkCheckBox(self, text="",  variable=self.check_var, command=self.checkbox_event, onvalue="on", offvalue="off")
        self.checkbox.grid(row=2, column=3)

        self.login_button = customtkinter.CTkButton(
            self,
            corner_radius=2,
            border_width=0,
            text_color=("white", "#ffffff"),
            text="Connexion",
            command=lambda:self.connexion()
        )
        self.login_button.grid(row=3, column=2, padx=70)

        self.register_button = customtkinter.CTkButton(
            self,
            corner_radius=2,
            border_width=0,
            text_color=("white", "#ffffff"),
            text="Creer un compte ?",
            command=self.register_form
        )
        self.register_button.grid(row=4, column=1, pady=5, padx=10)

    def checkbox_event(self):
        if self.check_var.get() == "on":
            self.password_entry.configure(show='')
        else:
            self.password_entry.configure(show='*')

    def register_form(self):

        self.dismount_component()
        self.email = customtkinter.CTkLabel(self,  text="Email: ")
        self.email.grid(row=1, column=1, sticky=tk.W+tk.E, pady=10)

        self.email_value = tk.StringVar()
        self.email_entry = customtkinter.CTkEntry(
            self,
            width=250,
            corner_radius=2,
            placeholder_text="admin@gmail.com",
            textvariable=self.email_value,
        )
        self.email_entry.grid(row=1, column=2, sticky=tk.W,  pady=10)

        self.username = customtkinter.CTkLabel(self, text="Nom utilisateur: ")
        self.username.grid(row=2, column=1, sticky=tk.W+tk.E, pady=10)

        self.username_value = tk.StringVar()
        self.username_entry = customtkinter.CTkEntry(
            self,
            width=250,
            corner_radius=2,
            textvariable=self.username_value,
        )
        self.username_entry.grid(row=2, column=2, sticky=tk.W, pady=10)

        self.password_label = customtkinter.CTkLabel(self, text="Mot de passe: ")
        self.password_label.grid(row=3, column=1, sticky=tk.W+tk.E, pady=10)

        self.password_value = tk.StringVar()
        self.password_entry = customtkinter.CTkEntry(
            self,
            show="*",
            width=250,
            corner_radius=2,
            textvariable=self.password_value,
        )
        self.password_entry.grid(row=3, column=2, sticky=tk.W, pady=10)

        self.register_button = customtkinter.CTkButton(
            self,
            corner_radius=2,
            border_width=0,
            text_color=("white", "#ffffff"),
            text="Valider",
            command=self.register_user
        )
        self.register_button.grid(row=4, column=2, padx=70)
        self.go_back_button = customtkinter.CTkButton(
            self,
            corner_radius=2,
            border_width=0,
            text_color=("white", "#ffffff"),
            text="<-- Retour",
            command=self.go_back
        )
        self.go_back_button.grid(row=4, column=1)

    def connexion(self):
        email = self.email_value.get()
        password = self.password.get()

        if email == "" or password == "":
            showwarning("Warning", "remplir tous les champs")
        elif email and password:
            is_valid = self.validate(email)
            if not is_valid:
                showwarning("Warning", "format email invalide")
            else:
                user = User(
                    username = None,
                    email = email,
                    password = password
                )
                is_login = self.controller.user_login(user)
                if is_login == None:
                    showwarning("Warning", "Utilisateur n'existe pas")
                elif is_login == True:
                    self.is_destroy = True
                    self.user_login = self.controller.update_user_last_login(email)
                    self.destroy()
                elif is_login == False:
                    showerror("Errror", "email/mot de passe incorrect")

    def register_user(self):
        username = self.username_value.get()
        email = self.email_value.get()
        password = self.password_value.get()

        if username == "" or email == "" or password == "":
            showwarning("Warning", "remplir tous les champs")
        elif username and email and password:
            is_valid = self.validate(email)
            if len(password) < 8:
                showwarning("Warning", "mot de passe court, 8 caracteres au minimum")
            elif is_valid:
                new_user = User(
                    username = username,
                    email = email,
                    password = password
                )
                is_register = self.controller.register_user(new_user)
                if is_register: showinfo("Success", "enregistrer avec succes")
                else: showwarning("Warning", "Utilisateur existe deja")

            elif not is_valid:
                showerror("Error", "Email invalide")


if __name__ == "__main__":
    app = AuthForm()
    app.mainloop()
