from tkinter.messagebox import showerror

from authentication.views.user_form import AuthForm
from custom_tk import App


def launch_app():
    main_app = AuthForm()
    main_app.mainloop()
    if main_app.is_destroy:
        name = main_app.user_login
        try:
            app = App(name)
            app.mainloop()
        except Exception as err:
            showerror("Erreur", str(err))


# -------launch application)
launch_app()
