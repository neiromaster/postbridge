import os
import subprocess
import sys
import time
from typing import Any, Dict, Optional

import psutil
import yt_dlp

from .config import settings

BROWSER_EXECUTABLES = (
    {
        "firefox": "firefox.exe",
        "chrome": "chrome.exe",
        "edge": "msedge.exe",
    }
    if sys.platform == "win32"
    else {
        "firefox": "firefox",
        "chrome": "google-chrome",
        "edge": "microsoft-edge",
    }
)


def _restart_browser() -> None:
    """Restarts the browser to refresh cookies."""
    browser_name = settings.downloader.browser
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
    time.sleep(settings.downloader.browser_restart_wait_seconds)

    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] == executable:
            print(f"🛑 Закрываю {browser_name}...")
            proc.kill()
            proc.wait()
            break

    print("✅ Перезапуск завершен.")


def download_video(video_url: str) -> Optional[str]:
    """
    Download a video from a given URL using yt-dlp's browser cookie import,
    with a retry mechanism.
    """
    if not os.path.exists(settings.downloader.output_path):
        os.makedirs(settings.downloader.output_path)

    ydl_opts: Dict[str, Any] = settings.downloader.yt_dlp_opts.copy()
    ydl_opts.update(
        {
            "outtmpl": os.path.join(settings.downloader.output_path, "%(id)s.%(ext)s"),
            "cookiesfrombrowser": (settings.downloader.browser,),
            "quiet": True,
            "no_warnings": True,
            "verbose": False,
        }
    )

    retries = settings.downloader.retries.count
    delay = settings.downloader.retries.delay_seconds

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
