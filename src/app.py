import asyncio
import logging
import os
from datetime import datetime

from .config import settings
from .dto import Post
from .exceptions import GracefulShutdown
from .managers.telegram_client_manager import TelegramClientManager
from .managers.vk_client_manager import VKClientManager
from .managers.ytdlp_manager import YtDlpManager
from .state_manager import get_last_post_id, set_last_post_id

logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")


async def run_app(
    shutdown_event: asyncio.Event,
    vk_manager: VKClientManager,
    tg_manager: TelegramClientManager,
    ytdlp_manager: YtDlpManager,
) -> None:
    print("🚀 Запускаю бота vk-to-tg...")
    try:
        while not shutdown_event.is_set():
            print(f"\n🔍 {datetime.now().strftime('%H:%M:%S %Y-%m-%d')} | Начинаю новый цикл проверки...")
            for binding in settings.bindings:
                vk_config = binding.vk
                telegram_config = binding.telegram
                domain = vk_config.domain
                post_count = vk_config.post_count
                post_source = vk_config.post_source
                channel_ids = telegram_config.channel_ids

                last_known_id = await get_last_post_id(domain)
                print(f"\n📄 Проверяю группу {domain}...")

                wall_posts = await vk_manager.get_vk_wall(domain, post_count, post_source)
                new_posts = [p for p in wall_posts if p.id > last_known_id]

                if new_posts:
                    print(f"✅ Найдено {len(new_posts)} новых постов в {domain}.")
                    for post in sorted(new_posts, key=lambda p: p.id):
                        await process_post(post, domain, channel_ids, shutdown_event, ytdlp_manager, tg_manager)
                        await set_last_post_id(domain, post.id)
                        last_known_id = post.id

            print(f"\n🏁 Цикл завершен. Пауза {settings.app.wait_time_seconds} секунд...")
            await asyncio.sleep(settings.app.wait_time_seconds)

    except GracefulShutdown:
        print("🛑 Получен сигнал на завершение — выходим из run_app.")


async def process_post(
    post: Post,
    domain: str,
    channel_ids: list[str],
    shutdown_event: asyncio.Event,
    ytdlp_manager: YtDlpManager,
    tg_manager: TelegramClientManager,
) -> None:
    print(f"\n📄 Обрабатываю пост ID: {post.id} из {domain}...")
    post_text: str = post.text or ""
    video_url: str | None = None

    if post.attachments:
        for attachment in post.attachments:
            if attachment.type == "video" and attachment.video:
                video = attachment.video
                access_key_part = f"?access_key={video.access_key}" if video.access_key else ""
                video_url = f"https://vk.com/video{video.owner_id}_{video.id}{access_key_part}"
                print(f"📹 Найдено видео: {video_url}")
                break

    if video_url:
        try:
            downloaded_file_path = await ytdlp_manager.download_video(video_url)
        except asyncio.CancelledError as e:
            print("⏹️ Загрузка прервана пользователем.")
            raise GracefulShutdown() from e

        if shutdown_event.is_set():
            print("⏹️ Остановка запрошена — прерываю обработку поста.")
            raise GracefulShutdown()

        if not downloaded_file_path:
            print("❌ Не удалось скачать видео. Перехожу к следующему посту.")
            return

        for channel_id in channel_ids:
            try:
                await tg_manager.send_video(channel_id, downloaded_file_path, post_text)
            except asyncio.CancelledError as e:
                print("⏹️ Отправка прервана пользователем.")
                raise GracefulShutdown() from e

        print("🗑️ Удаляю временный файл...")
        try:
            await asyncio.to_thread(os.remove, downloaded_file_path)
            print("✅ Файл удален.")
        except FileNotFoundError:
            print("⚠️ Файл уже удалён или не найден.")
        except Exception as e:
            print(f"❌ Ошибка удаления файла: {e}")
    else:
        print("🤷‍♂️ Видео в посте не найдено, пропускаю.")
