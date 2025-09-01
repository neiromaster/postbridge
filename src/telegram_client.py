import sys
import time
from pyrogram import Client
from .config import TELEGRAM_API_ID, TELEGRAM_API_HASH

SESSION_NAME = "user_session"


class Progress:
    def __init__(self):
        self.start_time = time.time()

    def __call__(self, current, total):
        now = time.time()
        elapsed = now - self.start_time
        speed_bps = current / elapsed if elapsed > 0 else 0
        speed_mbps = speed_bps * 8 / (1024 * 1024)

        percent = (current / total) * 100

        current_mb = current / (1024 * 1024)
        total_mb = total / (1024 * 1024)

        bar_length = 15
        filled_length = int(bar_length * current // total)
        bar = "█" * filled_length + "-" * (bar_length - filled_length)

        sys.stdout.write(f"\r[{bar}] {percent:5.1f}% | {current_mb:.1f} / {total_mb:.1f}MB | {speed_mbps:.1f}Mbps  ")
        sys.stdout.flush()


async def send_telegram_file(channel, file_path, caption):
    """Connects and sends a file to a Telegram channel via a user account."""
    print("Initializing Telegram client...")
    app = Client(SESSION_NAME, api_id=int(TELEGRAM_API_ID), api_hash=TELEGRAM_API_HASH)
    print("Connecting to Telegram...")
    async with app:
        print("Connection successful. Sending file...")

        await app.send_video(
            chat_id=channel,
            video=file_path,
            caption=caption,
            progress=Progress(),
        )
        sys.stdout.write("\n")
        print(f"File '{file_path}' sent successfully to channel '{channel}'.")
