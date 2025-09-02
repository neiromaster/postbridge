import os
import time
import yt_dlp
from .config import (
    DOWNLOADER_BROWSER,
    DOWNLOADER_OUTPUT_PATH,
    YTDLP_OPTS,
)


def download_video(video_url, retries=3, delay=10):
    """
    Download a video from a given URL using yt-dlp's browser cookie import,
    with a retry mechanism.
    """
    if not os.path.exists(DOWNLOADER_OUTPUT_PATH):
        os.makedirs(DOWNLOADER_OUTPUT_PATH)

    ydl_opts = YTDLP_OPTS.copy()
    ydl_opts.update(
        {
            "outtmpl": os.path.join(DOWNLOADER_OUTPUT_PATH, "%(id)s.%(ext)s"),
            "cookies-from-browser": DOWNLOADER_BROWSER,
            "quiet": True,
            "no_warnings": True,
            "verbose": False,
        }
    )

    for i in range(retries):
        print(f"📥 Скачиваю видео (попытка {i + 1}/{retries})...")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                downloaded_file = ydl.prepare_filename(info)
                print(f"✅ Видео скачано: {downloaded_file}")
                return downloaded_file
        except Exception as e:
            print(f"❌ Ошибка скачивания: {e}")
            if i < retries - 1:
                current_delay = delay * (2**i)
                print(f"⏳ Пауза {current_delay} секунд перед следующей попыткой...")
                time.sleep(current_delay)

    print(f"❌ Не удалось скачать видео после {retries} попыток.")
    return None
