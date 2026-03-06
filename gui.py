import customtkinter as ctk
from config import APP_NAME, APP_DIR, VERSION

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
        self.minsize(300, 200)
        
        # إنشاء هيكل النافذة (Sidebar and Main Content)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.sidebar.grid_rowconfigure(8, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="TimeSync", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.sync_button = ctk.CTkButton(self.sidebar, text="Sync Now", command=self.handle_sync)
        self.sync_button.grid(row=1, column=0, padx=20, pady=10)

        self.status_label = ctk.CTkLabel(self.sidebar, text="Status: Ready", font=ctk.CTkFont(size=12))
        self.status_label.grid(row=7, column=0, padx=20, pady=20)

        self.version_label = ctk.CTkLabel(
            self.sidebar,
            text=f"v{VERSION}",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.version_label.grid(row=9, column=0, pady=(0, 10))

        # --- Main Content ---
        self.main_frame = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.main_label = ctk.CTkLabel(self.main_frame, text="System Settings", font=ctk.CTkFont(size=24, weight="bold"))
        self.main_label.pack(pady=(0, 20), anchor="w")

        # --- Switches (Cards) ---
        self.create_setting_card("Run at Startup", self.logic['startup_exists'](), self.toggle_startup)
        self.create_setting_card("Sync on Wake (Resume)", self.logic['resume_exists'](), self.toggle_resume)
        self.create_setting_card("Show Notifications", True, self.toggle_notifications)

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

    def toggle_startup(self, switch):
        if switch.get():
            self.logic['cmd_startup_enable']()
        else:
            self.logic['cmd_startup_disable']()

    def toggle_resume(self, switch):
        if switch.get():
            self.logic['cmd_resume_enable']()
        else:
            self.logic['cmd_resume_disable']()

    def toggle_notifications(self, switch):
        # هنا تربطها مع تعديل ملف الـ settings.json
        pass

def run_gui():
    # هنا نمرر الدوال من الكود الأصلي للواجهة
    from TimeSync import cmd_now, cmd_startup_enable, cmd_startup_disable, startup_exists, resume_exists, cmd_resume_enable, cmd_resume_disable
    
    logic_map = {
        'cmd_now': cmd_now,
        'cmd_startup_enable': cmd_startup_enable,
        'cmd_startup_disable': cmd_startup_disable,
        'startup_exists': startup_exists,
        'resume_exists': resume_exists,
        'cmd_resume_enable': cmd_resume_enable,
        'cmd_resume_disable': cmd_resume_disable
    }
    
    app = TimeSyncGUI(logic_map)
    app.mainloop()

if __name__ == "__main__":
    run_gui()