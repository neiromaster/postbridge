import os
import browser_cookie3
import yt_dlp


def download_video(video_url, output_path="downloads"):
    """Download a video from a given URL."""
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    cookies = browser_cookie3.load()

    ydl_opts = {
        "outtmpl": os.path.join(output_path, "% (id)s.%(ext)s"),
        "cookiefile": "cookies.txt",
    }

    # Save cookies to a temporary file for yt-dlp
    with open("cookies.txt", "w") as f:
        for cookie in cookies:
            if cookie.domain == ".vk.com":
                f.write(
                    f"{cookie.domain}\tTRUE\t{cookie.path}\t{cookie.secure}\t"
                    f"{int(cookie.expires) if cookie.expires else 0}\t{cookie.name}\t{cookie.value}\n"
                )

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            downloaded_file = ydl.prepare_filename(info)
            return downloaded_file
    finally:
        # Clean up the temporary cookies file
        if os.path.exists("cookies.txt"):
            os.remove("cookies.txt")
