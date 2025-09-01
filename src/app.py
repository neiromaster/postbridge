import os
import time
import traceback

from .vk_client import get_vk_wall
from .downloader import download_video
from .telegram_client import send_telegram_file
from .state_manager import get_last_post_id, set_last_post_id


async def run_app():
    """Runs the main application logic."""
    print("--- Starting vk-to-tg bot ---")
    last_known_id = get_last_post_id()

    while True:
        print("\n--- Starting new check cycle ---")
        try:
            wall_posts = get_vk_wall()
            new_posts = [post for post in wall_posts if post["id"] > last_known_id]

            if not new_posts:
                print("No new posts found.")
            else:
                print(f"Found {len(new_posts)} new posts.")
                # Process posts from oldest to newest to maintain order
                for post in sorted(new_posts, key=lambda x: x["id"]):
                    print(f"\nProcessing post ID: {post['id']}...")
                    post_text = post["text"]
                    video_url = None

                    if "attachments" in post:
                        print("Searching for video attachments...")
                        for attachment in post["attachments"]:
                            if attachment["type"] == "video":
                                owner_id = attachment["video"]["owner_id"]
                                video_id = attachment["video"]["id"]
                                access_key = attachment["video"].get("access_key", "")
                                video_url = f"https://vk.com/video{owner_id}_{video_id}?access_key={access_key}"
                                print(f"Found video URL: {video_url}")
                                break
                        if not video_url:
                            print("No video attachment found in this post.")
                    else:
                        print("Post has no attachments.")

                    if video_url:
                        downloaded_file_path = download_video(video_url)

                        print("Preparing to send to Telegram...")
                        channel_id = os.getenv("TELEGRAM_CHANNEL_ID")
                        try:
                            # Convert to int if it's a numeric ID
                            channel_id = int(channel_id)
                            print(f"Using numeric channel ID: {channel_id}")
                        except (ValueError, TypeError):
                            print(f"Using channel username: {channel_id}")
                            pass
                        await send_telegram_file(
                            channel_id, downloaded_file_path, post_text
                        )

                        print(f"Cleaning up downloaded file: {downloaded_file_path}")
                        os.remove(downloaded_file_path)
                        print("Cleanup complete.")

                    # Update last known ID after each post is processed
                    set_last_post_id(post["id"])
                    last_known_id = post["id"]
                    print(f"Updated last known post ID to: {last_known_id}")

        except Exception as e:
            print(f"\n---! An error occurred: {e} !---")
            print("--- TRACEBACK ---")
            traceback.print_exc()
            print("-----------------")

        print("\n--- Cycle finished. Waiting for 60 seconds... ---")
        time.sleep(60)
