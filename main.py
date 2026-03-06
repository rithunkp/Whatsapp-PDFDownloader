import os
import sys
import customtkinter as ctk
from bot import WhatsAppBot

# Set up appearance for modern look
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("WhatsApp PDF Downloader")
        self.geometry("650x550")
        self.resizable(False, False)
        
        self.bot = None
        self.bot_thread = None
        self.download_dir = ""

        # configure grid layout 
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Title Label
        self.title_label = ctk.CTkLabel(self, text="WhatsApp PDF Downloader", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Input Frame
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)

        self.group_label = ctk.CTkLabel(self.input_frame, text="Group/Chat Name:", font=ctk.CTkFont(size=14))
        self.group_label.grid(row=0, column=0, padx=10, pady=10)

        self.group_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Enter exactly as it appears in WhatsApp")
        self.group_entry.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="ew")

        # Options Frame
        self.options_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.options_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")
        self.options_frame.grid_columnconfigure(1, weight=1)

        self.dir_button = ctk.CTkButton(self.options_frame, text="Choose Download Folder", command=self.pick_directory)
        self.dir_button.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.dir_label = ctk.CTkLabel(self.options_frame, text="Default (in app folder)", text_color="gray")
        self.dir_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        self.scroll_var = ctk.BooleanVar(value=False)
        self.scroll_switch = ctk.CTkSwitch(self.options_frame, text="Auto-Scroll for Older PDFs", variable=self.scroll_var)
        self.scroll_switch.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        # Buttons Frame
        self.button_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 10))

        self.start_button = ctk.CTkButton(self.button_frame, text="Start Bot", command=self.start_bot, fg_color="#2ecc71", hover_color="#27ae60", text_color="white")
        self.start_button.grid(row=0, column=0, padx=10)

        self.stop_button = ctk.CTkButton(self.button_frame, text="Stop Bot", command=self.stop_bot, state="disabled", fg_color="#e74c3c", hover_color="#c0392b", text_color="white")
        self.stop_button.grid(row=0, column=1, padx=10)

        # Console Text Area
        self.console = ctk.CTkTextbox(self, state="disabled", font=ctk.CTkFont(family="Consolas", size=12))
        self.console.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")

    def pick_directory(self):
        folder = ctk.filedialog.askdirectory()
        if folder:
            self.download_dir = folder
            self.dir_label.configure(text=folder)

    def log_message(self, message):
        # We must use after() to update GUI safely from the bot's background thread
        self.after(0, self._append_log, str(message))

    def _append_log(self, message):
        self.console.configure(state="normal")
        self.console.insert("end", message + "\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def start_bot(self):
        group_name = self.group_entry.get().strip()
        if not group_name:
            self.log_message("Error: Please enter a Group or Chat Name.")
            return

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.group_entry.configure(state="disabled")
        self.dir_button.configure(state="disabled")
        self.scroll_switch.configure(state="disabled")
        
        if self.download_dir:
            download_folder = self.download_dir
        else:
            if getattr(sys, 'frozen', False):
                application_path = os.path.dirname(sys.executable)
            else:
                application_path = os.path.dirname(os.path.abspath(__file__))
            download_folder = os.path.join(application_path, "downloads")
        
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)

        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")
        
        auto_scroll = self.scroll_var.get()
        scroll_status = "Enabled" if auto_scroll else "Disabled"
        
        self.log_message(f"PDFs will be downloaded to:\n{download_folder}\n")
        self.log_message(f"Auto-scroll is {scroll_status}")
        self.log_message(f"Starting bot for group: {group_name}")
        
        self.bot = WhatsAppBot(download_folder, log_callback=self.log_message, auto_scroll=auto_scroll)
        self.bot_thread = self.bot.start_in_thread(group_name)

        # Start checking if thread is alive
        self.after(1000, self.check_thread)

    def stop_bot(self):
        if self.bot:
            self.bot.stop()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.group_entry.configure(state="normal")
        self.dir_button.configure(state="normal")
        self.scroll_switch.configure(state="normal")
        self.log_message("User requested stop.")

    def check_thread(self):
        if self.bot_thread and not self.bot_thread.is_alive():
            if self.bot and self.bot.running:
                self.bot.running = False
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.group_entry.configure(state="normal")
            self.dir_button.configure(state="normal")
            self.scroll_switch.configure(state="normal")
            self.log_message("Bot process ended.")
        elif self.bot and self.bot.running:
            self.after(1000, self.check_thread)

    def on_closing(self):
        self.log_message("Closing application...")
        if self.bot:
            self.bot.stop()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
