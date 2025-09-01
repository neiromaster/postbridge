import os
import sys
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_NAME = "user_session"

if not API_ID or not API_HASH:
    raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file")

print("Initializing Telegram client...")

workers = os.cpu_count()
print(f"Using {workers} workers for Telegram uploads.")
client = TelegramClient(SESSION_NAME, int(API_ID), API_HASH, connection_retries=5, retry_delay=1)
print("Telegram client initialized.")


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
    print("Connecting to Telegram...")
    async with client:
        print("Connection successful. Sending file...")
        await client.send_file(
            entity=channel,
            file=file_path,
            caption=caption,
            allow_cache=False,
            part_size_kb=1024,
            progress_callback=progress_callback,
            workers=workers
        )
        sys.stdout.write('\n')
        print(f"File '{file_path}' sent successfully to channel '{channel}'.")
