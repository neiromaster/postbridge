import asyncio
import os
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import settings
from .downloader import download_video
from .state_manager import get_last_post_id, set_last_post_id
from .telegram_client import send_telegram_file
from .vk_client import get_vk_wall

# Type alias for a VK post dictionary
Post = Dict[str, Any]


async def run_app() -> None:
    """Runs the main application logic."""
    print("🚀 Запускаю бота vk-to-tg...")

    while True:
        print(f"\n🔍 {datetime.now().strftime('%H:%M:%S %Y-%m-%d')} | Начинаю новый цикл проверки...")
        for binding in settings.bindings:
            vk_config = binding.vk
            telegram_config = binding.telegram
            domain: str = vk_config.domain
            post_count: int = vk_config.post_count
            post_source: str = vk_config.post_source
            channel_ids: List[str] = telegram_config.channel_ids

            last_known_id: int = get_last_post_id(domain)
            print(f"\n📄 Проверяю группу {domain}...")

            try:
                wall_posts: List[Post] = get_vk_wall(domain, post_count, post_source)
                new_posts: List[Post] = [post for post in wall_posts if post["id"] > last_known_id]

                if new_posts:
                    print(f"✅ Найдено {len(new_posts)} новых постов в {domain}.")
                    for post in sorted(new_posts, key=lambda x: x["id"]):
                        print(f"\n📄 Обрабатываю пост ID: {post['id']} из {domain}...")
                        post_text: str = post.get("text", "")
                        video_url: Optional[str] = None

                        if "attachments" in post:
                            for attachment in post["attachments"]:
                                if attachment["type"] == "video":
                                    owner_id: int = attachment["video"]["owner_id"]
                                    video_id: int = attachment["video"]["id"]
                                    access_key: str = attachment["video"].get("access_key", "")
                                    video_url = f"https://vk.com/video{owner_id}_{video_id}?access_key={access_key}"
                                    print(f"📹 Найдено видео: {video_url}")
                                    break

                        if video_url:
                            downloaded_file_path = download_video(video_url)
                            if downloaded_file_path:
                                for channel_id in channel_ids:
                                    try:
                                        channel_id_int = int(channel_id)
                                        await send_telegram_file(channel_id_int, downloaded_file_path, post_text)
                                    except (ValueError, TypeError):
                                        await send_telegram_file(channel_id, downloaded_file_path, post_text)
                                print("🗑️ Удаляю временный файл...")
                                os.remove(downloaded_file_path)
                                print("✅ Файл удален.")
                        else:
                            print("🤷‍♂️ Видео в посте не найдено, пропускаю.")

                        set_last_post_id(domain, post["id"])
                        last_known_id = post["id"]

            except Exception as e:
                print(f"\n---! ❌ Произошла ошибка при обработке {domain}: {e} !---")
                print("--- TRACEBACK ---")
                traceback.print_exc()
                print("-----------------")

        print(f"\n🏁 Цикл завершен. Пауза {settings.app.wait_time_seconds} секунд...")
        await asyncio.sleep(settings.app.wait_time_seconds)
