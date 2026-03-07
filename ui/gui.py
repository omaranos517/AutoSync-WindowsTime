import os
import customtkinter as ctk

from config import APP_NAME, APP_DIR, VERSION, LOG_FILE, STARTUP_TASK_NAME, RESUME_TASK_NAME

# إعداد المظهر العام
ctk.set_appearance_mode("System")  # يتبع نظام الويندوز (فاتح أو غامق)
ctk.set_default_color_theme("blue") 

class TimeSyncGUI(ctk.CTk):
    def __init__(self, main_logic_functions):
        super().__init__()
        
        self.logic = main_logic_functions
        
        # إعدادات النافذة
        self.title(APP_NAME)
        icon = APP_DIR / "icon.ico"
        if icon.exists():
            self.iconbitmap(str(icon))
        self.geometry("600x450")
        self.minsize(520, 250)
        
        # إنشاء هيكل النافذة (Sidebar and Main Content)
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

        self.open_log_button = ctk.CTkButton(self.sidebar, text="Open Log File", command=self.open_log_file)
        self.open_log_button.grid(row=2, column=0, padx=20, pady=10)

        self.status_label = ctk.CTkLabel(self.sidebar, text="Status: Ready", font=ctk.CTkFont(size=12))
        self.status_label.grid(row=7, column=0, padx=20, pady=20)

        self.version_label = ctk.CTkLabel(
            self.sidebar,
            text=f"v{VERSION}",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.footer_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.footer_frame.grid(row=9, column=0, sticky="sew", padx=0, pady=0)
        self.footer_frame.grid_columnconfigure(0, weight=1)
        self.footer_frame.grid_columnconfigure(1, weight=0)

        self.version_label.grid(in_=self.footer_frame, row=0, column=0, sticky="w")

        self.about_button = ctk.CTkButton(
            self.footer_frame,
            text="ⓘ",
            width=15,
            height=16,
            corner_radius=8,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#434343",
            hover_color="#6C6C6C",
            text_color="#202020",
            command=self.open_about_window
        )
        self.about_button.grid(row=0, column=1, sticky="se")

        # --- Main Content ---
        self.main_frame = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.main_label = ctk.CTkLabel(self.main_frame, text="System Settings", font=ctk.CTkFont(size=24, weight="bold"))
        self.main_label.pack(pady=(0, 20), anchor="w")

        # --- Switches (Cards) ---
        settings = self.logic['load_settings']()
        notifications_enabled = settings.get("notifications", True)

        self.create_setting_card("Run at Startup", self.logic['task_exists'](STARTUP_TASK_NAME), self.toggle_startup)
        self.create_setting_card("Sync on Wake (Resume)", self.logic['task_exists'](RESUME_TASK_NAME), self.toggle_resume)
        self.create_setting_card("Show Notifications", notifications_enabled, self.toggle_notifications)

    def create_setting_card(self, text, initial_state, command):
        card = ctk.CTkFrame(self.main_frame, fg_color=("#E5E5E5", "#2B2B2B"))
        card.pack(fill="x", pady=5, padx=5)
        
        lbl = ctk.CTkLabel(card, text=text, font=ctk.CTkFont(size=14))
        lbl.pack(side="left", padx=20, pady=15)
        
        switch = ctk.CTkSwitch(card, text="", command=lambda: command(switch), )
        if initial_state:
            switch.select()
        switch.pack(side="right", padx=20)

    # --- Handlers (الربط مع المنطق الخاص بك) ---
    def handle_sync(self):
        self.status_label.configure(text="Status: Syncing...", text_color="orange")
        self.update()
        try:
            self.logic['cmd_now']()
            self.status_label.configure(text="Status: Success", text_color="green")
        except:
            self.status_label.configure(text="Status: Failed", text_color="red")

    def open_log_file(self):
        try:
            if not LOG_FILE.exists():
                LOG_FILE.touch()
            os.startfile(str(LOG_FILE))
            self.status_label.configure(text="Status: Log opened", text_color="green")
        except:
            self.status_label.configure(text="Status: Failed to open log", text_color="red")

    def open_about_window(self):
        from .about_window import open_about_window
        open_about_window(self)

    def toggle_startup(self, switch):
        if switch.get():
            self.logic['cmd_toggle_startup']("enable")
        else:
            self.logic['cmd_toggle_startup']("disable")

    def toggle_resume(self, switch):
        if switch.get():
            self.logic['cmd_toggle_resume']("enable")
        else:
            self.logic['cmd_toggle_resume']("disable")

    def toggle_notifications(self, switch):
        if switch.get():
            self.logic['cmd_toggle_notify']("enable")
        else:
            self.logic['cmd_toggle_notify']("disable")

def run_gui():
    # هنا نمرر الدوال من الكود الأصلي للواجهة
    from TimeSync import cmd_now, task_exists, cmd_toggle_startup, cmd_toggle_resume, cmd_toggle_notify, load_settings
    
    logic_map = {
        'cmd_now': cmd_now,
        'cmd_toggle_startup': cmd_toggle_startup,
        'task_exists': task_exists,
        'cmd_toggle_resume': cmd_toggle_resume,
        'load_settings': load_settings,
        'cmd_toggle_notify': cmd_toggle_notify
    }
    
    app = TimeSyncGUI(logic_map)
    app.mainloop()

if __name__ == "__main__":
    run_gui()
