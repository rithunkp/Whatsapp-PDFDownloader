from bot import WhatsAppBot
import os

def main():
    GROUP_NAME = input("WhatsApp Group Name: ")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    download_folder = os.path.join(current_dir, "downloads")
    
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    
    print(f"PDFs will be downloaded to: {download_folder}")
    
    bot = WhatsAppBot(download_folder)
    bot.run(GROUP_NAME)

if __name__ == "__main__":
    main()
