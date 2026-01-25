import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class WhatsAppBot:
    def __init__(self, download_path):
        self.download_path = os.path.abspath(download_path)
        
        self.options = Options()
        self.user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
        self.options.add_argument(f"user-data-dir={self.user_data_dir}")
        
        self.options.add_experimental_option("prefs", {
            "download.default_directory": self.download_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        })
        self.options.add_argument("--start-maximized")
        self.options.add_experimental_option("detach", True)

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        self.wait = WebDriverWait(self.driver, 60)
        self.processed_files = set()

    def login(self):
        self.driver.get("https://web.whatsapp.com")
        
        try:
            self.wait.until(EC.presence_of_element_located((By.ID, "side")))
            print("Login successful (or session restored)!")
        except Exception as e:
            print("Login timed out. Please scan the QR code if needed.")

    def open_group(self, group_name):
        print(f"Searching for group: {group_name}")
        try:
            search_box = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')))
            search_box.clear()
            search_box.send_keys(group_name)
            search_box.send_keys(Keys.ENTER)
            time.sleep(30)
            print(f"Opened group: {group_name}")
        except Exception as e:
            print(f"Failed to open group: {group_name}. It might not exist or took too long.")
            print(e)



    def download_unread_pdfs(self, check_limit=10):
        
        try:
            pdf_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '.pdf')]")
            
            valid_pdfs = []
            for el in pdf_elements:
                try:
                    text = el.text.strip()
                    if text.lower().endswith('.pdf'):
                        if el.is_displayed():
                            valid_pdfs.append(el)
                except:
                    pass
            
            if not valid_pdfs:
                print("No obvious PDF text elements found. Checking titles...")
                title_elements = self.driver.find_elements(By.XPATH, "//*[contains(@title, '.pdf')]")
                valid_pdfs.extend(title_elements)

            if not valid_pdfs:
                print("No PDF files found in visible area.")
                return

            print(f"Found {len(valid_pdfs)} potential PDF markers.")
            
            for element in valid_pdfs:
                try:
                    filename = element.text or element.get_attribute('title') or "unknown.pdf"
                    
                    if filename in self.processed_files:
                        continue
                        
                    print(f"Attempting to download: {filename}")
                    
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
                            print("Downloaded.")
                            
                    time.sleep(2)
                    self.processed_files.add(filename)
                    
                except Exception as e:
                    print(f"Error handling file {filename}: {e}")
                    
        except Exception as e:
            print(f"Error scanning for PDFs: {e}")

    def run(self, group_name):
        self.login()
        self.open_group(group_name)
        
        print("Press Ctrl+C to stop.")
        try:
            while True:
                self.download_unread_pdfs()
                time.sleep(10)
        except KeyboardInterrupt:
            print("Stopping")
            self.driver.quit()
