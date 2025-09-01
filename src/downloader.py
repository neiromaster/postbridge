import os
import yt_dlp


def download_video(video_url, output_path="downloads"):
    """Download a video from a given URL using yt-dlp's browser cookie import."""
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    browser_for_cookies = "edge"

    print(f"Attempting to use cookies from {browser_for_cookies}...")

    ydl_opts = {
        "outtmpl": os.path.join(output_path, "%(id)s.%(ext)s"),
        "cookies-from-browser": (browser_for_cookies, ),
        "concurrent_fragments": 4,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        downloaded_file = ydl.prepare_filename(info)
        return downloaded_file