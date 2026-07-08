import threading
import customtkinter as ctk

from config import APP_NAME, APP_DIR, VERSION, STARTUP_TASK_NAME, PERIODIC_TASK_NAME, RESUME_TASK_NAME

# Global appearance configuration
ctk.set_appearance_mode("System")  # Follow the Windows light/dark appearance
ctk.set_default_color_theme("blue") 

# Custom colors
# VARIABLE_NAME = (light_mode_color, dark_mode_color)
INFO_BLUE = ("#4B6B8A", "#A9C4E2")
SUCCESS_GREEN = ("#2E7D4F", "#7FDFA1")
WARNING_AMBER = ("#A56A00", "#E7C15A")
ERROR_RED = ("#A94442", "#E58B8B")

class TimeSyncGUI(ctk.CTk):
    def __init__(self, main_logic_functions):
        super().__init__()
        
        self.logic = main_logic_functions
        self.sync_in_progress = False
        self._is_destroyed = False
        self._sync_thread = None
        
        # Window configuration
        self.title(APP_NAME)
        icon = APP_DIR / "icon.ico"
        if icon.exists():
            self.iconbitmap(str(icon))
        self.geometry("600x450")
        self.minsize(520, 250)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Build the main window layout (sidebar and main content)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_columnconfigure(0, weight=1)

        self.sidebar.grid_rowconfigure(8, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="TimeSync", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.sync_button = ctk.CTkButton(self.sidebar, text="Sync Now", command=self.handle_sync)
        self.sync_button.grid(row=1, column=0, padx=20, pady=10)

        self.open_log_button = ctk.CTkButton(self.sidebar, text="Open Log File", command=lambda: [self.logic['open_logs'](), self.update_status("Status: Opening log file...", INFO_BLUE)])
        self.open_log_button.grid(row=2, column=0, padx=20, pady=10)

        self.status_label = ctk.CTkLabel(
            self.sidebar,
            text=f"{self.internet_status()}",
            font=ctk.CTkFont(size=12),
            wraplength=120,
            justify="center",
            anchor="center"
        )
        self.status_label.grid(row=7, column=0, padx=20, pady=20, sticky="ew")

        self.version_label = ctk.CTkLabel(
            self.sidebar,
            text=f"v{VERSION}",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.footer_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.footer_frame.grid(row=9, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.footer_frame.grid_rowconfigure(0, weight=1)
        self.footer_frame.grid_columnconfigure(0, weight=1)
        self.footer_frame.grid_columnconfigure(1, weight=0)

        self.version_label.grid(in_=self.footer_frame, row=0, column=0, sticky="sw")

        self.about_button = ctk.CTkButton(
            self.footer_frame,
            text="ⓘ",
            width=10,
            height=20,
            corner_radius=100,
            border_spacing=0,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#434343",
            hover_color="#6C6C6C",
            text_color="#202020",
            command=self.open_about_window
        )
        self.about_button.grid(row=0, column=1, sticky="se", padx=(8, 0))

        # --- Main Content ---
        self.main_frame = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.main_label = ctk.CTkLabel(self.main_frame, text="System Settings", font=ctk.CTkFont(size=24, weight="bold"))
        self.main_label.pack(pady=(0, 20), anchor="w")

        # --- Switches (Cards) ---
        # settings = self.logic['load_settings']()
        # notifications_enabled = settings.get("notifications", True)

        status = self.logic['get_stetus']()

        self.create_setting_card("Run at Startup", status['startUp'], self.toggle_startup)
        self.create_setting_card("Periodic Sync (Hourly)", status['periodic'], self.toggle_periodic)
        self.create_setting_card("Sync on Wake (Sleep/Hibernation)", status['resume'], self.toggle_resume)
        self.create_setting_card("Show Notifications", status['notify'], self.toggle_notifications)

    def create_setting_card(self, text, initial_state, command):
        card = ctk.CTkFrame(self.main_frame, fg_color=("#E5E5E5", "#2B2B2B"))
        card.pack(fill="x", pady=5, padx=5)
        
        lbl = ctk.CTkLabel(card, text=text, font=ctk.CTkFont(size=14))
        lbl.pack(side="left", padx=20, pady=15)
        
        switch = ctk.CTkSwitch(card, text="", command=lambda: command(switch), )
        if initial_state:
            switch.select()
        switch.pack(side="right", padx=20)

    def on_closing(self):
        self._is_destroyed = True
        self.destroy()

    def update_status(self, text, color):
        """Only update status if the window is not destroyed to avoid errors."""
        if not self._is_destroyed:
            self.after(0, lambda: self.status_label.configure(text=text, text_color=color))
        else:
            try:
                from utils.notifySystem import send_notification
                send_notification(
                    "TimeSync Status Update",
                    text,
                    tag="sync-status",
                    group="sync-status"
                )
            except ImportError:
                pass

    def internet_status(self):
        if self.logic['has_internet_connection']():
            return "Status: Ready to sync"
        else:
            return "Status: No internet connection"

    def handle_sync(self):
        if self.sync_in_progress:
            return

        self.sync_in_progress = True
        self.sync_button.configure(state="disabled")
        self.status_label.configure(text="Status: Syncing...", text_color=WARNING_AMBER)

        self._sync_thread = threading.Thread(target=self._sync_worker)
        self._sync_thread.start()

    def _sync_worker(self):
        try:
            sync_result = self.logic['sync_time_action'](silent=True)

            color = SUCCESS_GREEN if "Success" in sync_result else ERROR_RED
            if "Warning" in sync_result: color = WARNING_AMBER

            self.update_status(sync_result, color)
            
        except Exception:
            self.update_status("Status: Failed", ERROR_RED)
        finally:
            if not self._is_destroyed:
                self.after(0, self._finish_sync)
            else:
                self._finish_sync()

    def _finish_sync(self):
        self.sync_in_progress = False
        self._sync_thread = None
        if not self._is_destroyed:
            self.sync_button.configure(state="normal")

    def _toggle_feature(self, feature_name : str, switch):
        if switch.get():
            self.logic[f'toggle_{feature_name}']("enable")
            self.update_status(f"Status: {feature_name.capitalize()} sync enabled", SUCCESS_GREEN)
        else:
            self.logic[f'toggle_{feature_name}']("disable")
            self.update_status(f"Status: {feature_name.capitalize()} sync disabled", ERROR_RED)

    def open_about_window(self):
        from .about_window import open_about_window
        self.update_status("Status: Opening About Window...", INFO_BLUE)
        open_about_window(self)

    def toggle_startup(self, switch):
        self._toggle_feature("startup", switch)

    def toggle_periodic(self, switch):
        self._toggle_feature("periodic", switch)

    def toggle_resume(self, switch):
        self._toggle_feature("resume", switch)

    def toggle_notifications(self, switch):
        self._toggle_feature("notifications", switch)

def run_gui():
    # Pass the existing application functions into the GUI layer.
    from core.actions import sync_time_action, get_status, toggle_startup, toggle_periodic, toggle_resume, toggle_notify, open_logs
    from core.internet_check import has_internet_connection
    
    logic_map = {
        'sync_time_action': sync_time_action,
        'open_logs': open_logs,
        'toggle_startup': toggle_startup,
        'toggle_periodic': toggle_periodic,
        'toggle_resume': toggle_resume,
        'get_status': get_status,
        'toggle_notifications': toggle_notify,
        'has_internet_connection': has_internet_connection
    }
    
    app = TimeSyncGUI(logic_map)
    app.mainloop()

if __name__ == "__main__":
    run_gui()
