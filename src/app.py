import os
import time
import traceback

from .vk_client import get_vk_wall
from .downloader import download_video
from .telegram_client import send_telegram_file
from .state_manager import get_last_post_id, set_last_post_id


async def run_app():
    """Runs the main application logic."""
    print("Starting vk-to-tg bot...")
    last_known_id = get_last_post_id()
    print(f"Last known post ID: {last_known_id}")

    while True:
        try:
            wall_posts = get_vk_wall()
            new_posts = [post for post in wall_posts if post["id"] > last_known_id]

            if not new_posts:
                print("No new posts found.")
            else:
                for post in sorted(new_posts, key=lambda x: x["id"], reverse=True):
                    print(f"Found new post: {post['id']}")
                    post_text = post["text"]
                    video_url = None

                    if "attachments" in post:
                        for attachment in post["attachments"]:
                            if attachment["type"] == "video":
                                owner_id = attachment["video"]["owner_id"]
                                video_id = attachment["video"]["id"]
                                access_key = attachment["video"].get("access_key", "")
                                video_url = f"https://vk.com/video{owner_id}_{video_id}?access_key={access_key}"
                                break

                    if video_url:
                        print(f"Downloading video from {video_url}...")
                        downloaded_file_path = download_video(video_url)
                        print(f"Video downloaded to {downloaded_file_path}")

                        print("Sending to Telegram...")
                        channel_id = os.getenv("TELEGRAM_CHANNEL_ID")
                        try:
                            channel_id = int(channel_id)
                        except (ValueError, TypeError):
                            pass
                        await send_telegram_file(channel_id, downloaded_file_path, post_text)
                        print("Post sent to Telegram.")

                        os.remove(downloaded_file_path)

                    newest_id_in_batch = max(p["id"] for p in new_posts)
                    set_last_post_id(newest_id_in_batch)
                    last_known_id = newest_id_in_batch
                    print(f"Last post ID updated to: {last_known_id}")

        except Exception as e:
            print(f"An error occurred: {e}")
            print("--- TRACEBACK ---")
            traceback.print_exc()
            print("-----------------")

        print("Waiting for 60 seconds before next check...")
        time.sleep(60)
