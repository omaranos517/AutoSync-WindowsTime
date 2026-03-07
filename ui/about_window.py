import customtkinter as ctk
import webbrowser
from config import APP_NAME, VERSION, AUTHOR, GITHUB


def open_about_window(parent):
    about = ctk.CTkToplevel(parent)
    about.title("About")
    about.geometry("460x360")
    about.resizable(False, False)
    about.transient(parent)
    about.grab_set()

    container = ctk.CTkFrame(about, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=16, pady=16)

    app_label = ctk.CTkLabel(container, text=APP_NAME, font=ctk.CTkFont(size=24, weight="bold"))
    app_label.pack(pady=(2, 4))

    version_label = ctk.CTkLabel(container, text=f"Version {VERSION}", text_color="gray")
    version_label.pack()

    author_label = ctk.CTkLabel(container, text=f"By {AUTHOR}", font=ctk.CTkFont(size=13))
    author_label.pack(pady=(4, 12))

    description = (
        "TimeSync keeps your Windows clock accurate by forcing a time sync "
        "at startup or after wake-up (hibernate/sleep), reducing login/session drift issues."
    )
    description_label = ctk.CTkLabel(
        container,
        text=description,
        wraplength=410,
        justify="left",
        text_color=("#222222", "#DDDDDD"),
    )
    description_label.pack(fill="x", pady=(0, 10))

    features_title = ctk.CTkLabel(container, text="Highlights", font=ctk.CTkFont(size=13, weight="bold"))
    features_title.pack(anchor="w")

    features_text = (
        "- One-click manual sync\n"
        "- Optional sync at startup and resume\n"
        "- Built-in logging and notification support"
    )
    features_label = ctk.CTkLabel(container, text=features_text, justify="left")
    features_label.pack(anchor="w", pady=(2, 10))

    repo_label = ctk.CTkLabel(container, text="Project Repository", font=ctk.CTkFont(size=13, weight="bold"))
    repo_label.pack(anchor="w")

    link_text = ctk.CTkTextbox(container, height=52, wrap="word")
    link_text.insert("1.0", GITHUB)
    link_text.configure(state="disabled")
    link_text.pack(fill="x", pady=(2, 10))

    actions = ctk.CTkFrame(container, fg_color="transparent")
    actions.pack(fill="x", pady=(2, 0))
    actions.grid_columnconfigure((0, 1, 2), weight=1)

    open_repo_button = ctk.CTkButton(
        actions,
        text="Open on GitHub",
        command=lambda: webbrowser.open(GITHUB, new=2)
    )
    open_repo_button.grid(row=0, column=0, padx=4, sticky="ew")

    copy_repo_button = ctk.CTkButton(
        actions,
        text="Copy Link",
        command=lambda: (about.clipboard_clear(), about.clipboard_append(GITHUB))
    )
    copy_repo_button.grid(row=0, column=1, padx=4, sticky="ew")

    close_button = ctk.CTkButton(actions, text="Close", command=about.destroy)
    close_button.grid(row=0, column=2, padx=4, sticky="ew")
