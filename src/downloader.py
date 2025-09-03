import os
import subprocess
import sys
import time

import psutil
import yt_dlp

from .config import (
    DOWNLOADER_BROWSER,
    DOWNLOADER_OUTPUT_PATH,
    YTDLP_OPTS,
)

if sys.platform == "win32":
    BROWSER_EXECUTABLES = {
        "firefox": "firefox.exe",
        "chrome": "chrome.exe",
        "edge": "msedge.exe",
    }
else:
    BROWSER_EXECUTABLES = {
        "firefox": "firefox",
        "chrome": "google-chrome",
        "edge": "microsoft-edge",
    }


def _restart_browser():
    """Restarts the browser to refresh cookies."""
    browser_name = DOWNLOADER_BROWSER
    executable = BROWSER_EXECUTABLES.get(browser_name)

    if not executable:
        print(f"⚠️ Браузер {browser_name} не поддерживается для перезапуска.")
        return

    print(f"🔄 Перезапускаю {browser_name} для обновления cookie...")

    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] == executable:
            print(f"▶️ {browser_name} уже запущен. Закрываю...")
            proc.kill()
            proc.wait()

    print(f"🚀 Запускаю {browser_name}...")

    subprocess.Popen([executable])
    time.sleep(30)

    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] == executable:
            print(f"🛑 Закрываю {browser_name}...")
            proc.kill()
            proc.wait()
            break

    print("✅ Перезапуск завершен.")


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
            "cookiesfrombrowser": (DOWNLOADER_BROWSER,),
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
            if "This video is only available for registered users" in str(e) and i < retries - 1:
                _restart_browser()
                continue

            if i < retries - 1:
                current_delay = delay * (2**i)
                print(f"⏳ Пауза {current_delay} секунд перед следующей попыткой...")
                time.sleep(current_delay)

    print(f"❌ Не удалось скачать видео после {retries} попыток.")
    return None
