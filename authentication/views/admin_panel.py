import customtkinter


class AdminPanel(customtkinter.CTk):
    """ define admin interface """

    def __init__(self):
        super().__init__()
        self.title("Admin panel")
        self.geometry(f"{1129}x{675}")
        self.resizable(0, 0)
