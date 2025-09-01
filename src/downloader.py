import os
import yt_dlp


def download_video(video_url, output_path="downloads"):
    """Download a video from a given URL using yt-dlp's browser cookie import."""
    print(f"Ensuring download directory exists at '{output_path}'...")
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        print("Download directory created.")

    browser_for_cookies = "edge"
    print(f"Attempting to use cookies from '{browser_for_cookies}' browser...")

    ydl_opts = {
        "outtmpl": os.path.join(output_path, "%(id)s.%(ext)s"),
        "cookies-from-browser": (browser_for_cookies,),
        "concurrent_fragment_downloads": 5,
        "skip_unavailable_fragments": False,
        "fragment_retries": 50,
        "retries": 50,
        "external_downloader": {
            "default": "aria2c",
            "dash": "native",
            "m3u8": "native",
        },
        "external_downloader_args": {
            "aria2c": [
                "-x",
                "5",
                "-s",
                "5",
            ],
        },
        "quiet": True,
        "no_warnings": True,
        "verbose": False,
    }

    print("Starting video download with yt-dlp...")
    print(f"Download options: {ydl_opts}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        downloaded_file = ydl.prepare_filename(info)
        print(f"yt-dlp finished. File prepared at: {downloaded_file}")
        return downloaded_file
