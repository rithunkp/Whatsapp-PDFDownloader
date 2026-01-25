# WhatsApp PDF Downloader

A simple Python automation bot that monitors a specific WhatsApp Group and automatically downloads all PDF files sent to it.

## Features
- 🚀 Uses **Selenium** for WhatsApp Web automation.
- 📂 Automatically creates a `downloads` folder.
- 🔄 **Auto-detects** and downloads valid PDF files.
- 🧠 **Smart Deduplication**: Remembers downloaded files in the current session to avoid duplicates.
- 🛡️ Safe & Local: Runs entirely on your machine using your own Chrome browser.

## Prerequisites
- **Python 3.7+** installed.
- **Google Chrome** installed.
- A WhatsApp account (for WhatsApp Web).

## Installation

1.  Clone this repository or download the files.
2.  Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Run the script:

    ```bash
    python main.py
    ```

2.  Enter the **exact case-sensitive name** of the WhatsApp group you want to monitor when prompted.
3.  A Chrome window will open. **Scan the QR code** with your phone to log in to WhatsApp Web.
4.  The bot will automatically open the group and start checking for PDFs.
5.  Check the `downloads` folder for your files!

## Controls
- Press `Ctrl + C` in the terminal to stop the bot safely.

## Notes
- The browser window must remain open for the bot to check for files.
- You can minimize the window, but do not close it.
