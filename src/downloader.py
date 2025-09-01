import os
import yt_dlp
from .config import (
    DOWNLOADER_BROWSER,
    DOWNLOADER_OUTPUT_PATH,
    YTDLP_OPTS,
)


def download_video(video_url):
    """Download a video from a given URL using yt-dlp's browser cookie import."""
    print(f"Ensuring download directory exists at '{DOWNLOADER_OUTPUT_PATH}'...")
    if not os.path.exists(DOWNLOADER_OUTPUT_PATH):
        os.makedirs(DOWNLOADER_OUTPUT_PATH)
        print("Download directory created.")

    print(f"Attempting to use cookies from '{DOWNLOADER_BROWSER}' browser...")

    ydl_opts = YTDLP_OPTS.copy()
    ydl_opts.update(
        {
            "outtmpl": os.path.join(DOWNLOADER_OUTPUT_PATH, "%(id)s.%(ext)s"),
            "cookies-from-browser": (DOWNLOADER_BROWSER,),
            "quiet": True,
            "no_warnings": True,
            "verbose": False,
        }
    )

    print("Starting video download with yt-dlp...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        downloaded_file = ydl.prepare_filename(info)
        print(f"yt-dlp finished. File prepared at: {downloaded_file}")
        return downloaded_file
