import os
import sys
import time
import json
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class WhatsAppBot:
    def __init__(self, download_path, log_callback=None, auto_scroll=False):
        self.download_path = os.path.abspath(download_path)
        self.log_callback = log_callback if log_callback else print
        self.running = False
        self.auto_scroll = auto_scroll
        self.driver = None
        
        self.options = Options()

        # Determine correct base path whether running as script or pyinstaller executable
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        self.user_data_dir = os.path.join(base_dir, "chrome_profile")
        self.history_file = os.path.join(self.user_data_dir, "history.json")
        self.options.add_argument(f"user-data-dir={self.user_data_dir}")
        self.options.add_argument("--remote-allow-origins=*") # Prevent websocket connection errors
        
        self.options.add_experimental_option("prefs", {
            "download.default_directory": self.download_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        })
        self.options.add_argument("--start-maximized")
        self.options.add_experimental_option("detach", True)

        self.wait = None
        self.processed_files = self._load_history()

    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            except Exception as e:
                self.log(f"Warning: Could not read history file. {e}")
        return set()

    def _save_history(self, filename):
        self.processed_files.add(filename)
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.processed_files), f)
        except Exception as e:
            self.log(f"Warning: Could not save history file. {e}")

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)

    def login(self):
        self.log("Initializing Chrome driver...")
        try:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
            self.wait = WebDriverWait(self.driver, 60)
        except Exception as e:
            self.log(f"Error starting Chrome: {e}")
            return False

        self.driver.get("https://web.whatsapp.com")
        self.log("Waiting for WhatsApp Web to load...")
        
        try:
            self.wait.until(EC.presence_of_element_located((By.ID, "side")))
            self.log("Login successful (or session restored)!")
            return True
        except Exception as e:
            self.log("Login timed out. Please scan the QR code if needed.")
            return False

    def open_group(self, group_name):
        self.log(f"Searching for group: {group_name}")
        try:
            # Try multiple selectors for the search box as WhatsApp updates its web UI frequently
            search_box = None
            selectors = [
                (By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'),
                (By.XPATH, '//*[@title="Search input textbox"]'),
                (By.XPATH, '//div[contains(@class, "lexical-rich-text-input")]/div[@role="textbox"]')
            ]
            
            for by, val in selectors:
                try:
                    search_box = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((by, val)))
                    if search_box: break
                except:
                    continue
                    
            if not search_box:
                raise Exception("Could not find search box")

            search_box.clear()
            search_box.send_keys(group_name)
            time.sleep(2) # Wait for search results
            search_box.send_keys(Keys.ENTER)
            time.sleep(3) # Wait for chat to open
            self.log(f"Opened group: '{group_name}'")
            return True
        except Exception as e:
            self.log(f"Failed to open group: {group_name}. It might not exist or took too long.")
            self.log(str(e))
            return False

    def download_unread_pdfs(self):
        try:
            # Find elements containing text or title resembling .pdf
            pdf_elements = self.driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'PDF', 'pdf'), '.pdf')]")
            
            valid_pdfs = []
            for el in pdf_elements:
                try:
                    text = el.text.strip()
                    if text.lower().endswith('.pdf') and el.is_displayed():
                        valid_pdfs.append(el)
                except:
                    pass
            
            if not valid_pdfs:
                # Fallback to title attribute
                title_elements = self.driver.find_elements(By.XPATH, "//*[contains(translate(@title, 'PDF', 'pdf'), '.pdf')]")
                valid_pdfs.extend([el for el in title_elements if el.is_displayed()])

            if not valid_pdfs:
                return

            self.log(f"Found {len(valid_pdfs)} potential PDF markers in visible area.")
            
            for element in valid_pdfs:
                if not self.running:
                    break
                try:
                    filename = element.text or element.get_attribute('title') or ""
                    if not filename.lower().endswith('.pdf'):
                        # Guarantee uniqueness for missing names so they don't block subsequent unnamed downloads
                        filename = f"unknown_{int(time.time()*1000)}.pdf"
                    
                    if filename in self.processed_files:
                        continue
                        
                    self.log(f"Attempting to download: {filename}")
                    
                    parent = element.find_element(By.XPATH, "./..")
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(1)
                    
                    try:
                        element.click()
                    except:
                        try:
                            parent.click()
                        except:
                            self.driver.execute_script("arguments[0].click();", element)
                            
                    self.log(f"Clicked download for: {filename}")
                    time.sleep(2)
                    self._save_history(filename)
                    
                except Exception as e:
                    self.log(f"Error handling file {filename}: {e}")
                    
        except Exception as e:
            self.log(f"Error scanning for PDFs: {e}")

    def run(self, group_name):
        self.running = True
        if not self.login():
            self.running = False
            return
            
        if not self.open_group(group_name):
            self.running = False
            return
            
        self.log("Started monitoring for PDFs...")
        try:
            while self.running:
                if self.auto_scroll:
                    try:
                        # Find the scrollable message container and send the Page Up key
                        chat_container = self.driver.find_element(By.XPATH, '//div[@data-testid="conversation-panel-messages"]/parent::div')
                        if chat_container:
                            chat_container.send_keys(Keys.PAGE_UP)
                            time.sleep(1) # wait for DOM settling after scroll
                    except Exception as e:
                        pass # if it can't scroll, just ignore and try downloading
                        
                self.download_unread_pdfs()
                time.sleep(5)
        except Exception as e:
            self.log(f"Bot error: {e}")
        finally:
            self.stop()

    def stop(self):
        if self.running:
            self.running = False
            self.log("Stopping bot...")
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            self.log("Browser closed.")
        
    def start_in_thread(self, group_name):
        thread = threading.Thread(target=self.run, args=(group_name,), daemon=True)
        thread.start()
        return thread
