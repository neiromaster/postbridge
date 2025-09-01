import os
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_NAME = "user_session"

if not API_ID or not API_HASH:
    raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file")

client = TelegramClient(SESSION_NAME, int(API_ID), API_HASH)

async def send_telegram_file(channel, file_path, caption):
    """Connects and sends a file to a Telegram channel via a user account."""
    async with client:
        print("Sending file to Telegram via user account...")
        await client.send_file(
            entity=channel,
            file=file_path,
            caption=caption,
            allow_cache=False,
            part_size_kb=512
        )
        print("File sent successfully!")