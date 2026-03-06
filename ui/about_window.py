import customtkinter as ctk
from config import APP_NAME, VERSION, AUTHOR


def open_about_window(parent):
    about = ctk.CTkToplevel(parent)
    about.title("About")
    about.geometry("300x160")
    about.resizable(False, False)
    about.transient(parent)
    about.grab_set()

    app_label = ctk.CTkLabel(about, text=APP_NAME, font=ctk.CTkFont(size=20, weight="bold"))
    app_label.pack(pady=(18, 8))

    version_label = ctk.CTkLabel(about, text=f"Version {VERSION}", text_color="gray")
    version_label.pack()

    author_label = ctk.CTkLabel(about, text=f"By {AUTHOR}", font=ctk.CTkFont(size=12))
    author_label.pack(pady=(8, 8))

    close_button = ctk.CTkButton(about, text="Close", width=90, command=about.destroy)
    close_button.pack(pady=(6, 12))
