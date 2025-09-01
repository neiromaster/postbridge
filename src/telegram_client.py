import os
import sys
from pyrogram import Client
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_NAME = "user_session"

if not API_ID or not API_HASH:
    raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file")

def progress_callback(current, total):
    """Shows a progress bar in the console."""
    percentage = current * 100 / total
    bar_length = 50
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    sys.stdout.write(f'\rUploading: [{bar}] {percentage:.2f}%')
    sys.stdout.flush()


async def send_telegram_file(channel, file_path, caption):
    """Connects and sends a file to a Telegram channel via a user account."""
    print("Initializing Telegram client...")
    app = Client(SESSION_NAME, api_id=int(API_ID), api_hash=API_HASH)
    print("Connecting to Telegram...")
    async with app:
        print("Connection successful. Sending file...")
        await app.send_video(
            chat_id=channel,
            document=file_path,
            caption=caption,
            progress=progress_callback,
        )
        sys.stdout.write('\n')
        print(f"File '{file_path}' sent successfully to channel '{channel}'.")
