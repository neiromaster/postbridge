import os
import asyncio
from telegram import Bot
from telegram.ext import Application
from dotenv import load_dotenv

load_dotenv()

async def send_telegram_message(video_path, caption):
    """Send a video with a caption to a Telegram channel."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID")
    if not token or not channel_id:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID must be set in .env file")

    application = Application.builder().token(token).build()

    with open(video_path, 'rb') as video_file:
        await application.bot.send_video(
            chat_id=channel_id,
            video=video_file,
            caption=caption
        )

if __name__ == '__main__':
    # Example usage (for testing)
    # Make sure to have a test.mp4 file and .env configured
    # asyncio.run(send_telegram_message("test.mp4", "Hello from the bot!"))
    pass
