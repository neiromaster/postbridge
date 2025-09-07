import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path

from .config import settings
from .dto import Post
from .managers.telegram_client_manager import TelegramClientManager
from .managers.vk_client_manager import VKClientManager
from .managers.ytdlp_manager import YtDlpManager
from .printer import log
from .state_manager import get_last_post_id, set_last_post_id


async def run_app(
    shutdown_event: asyncio.Event,
    vk_manager: VKClientManager,
    tg_manager: TelegramClientManager,
    ytdlp_manager: YtDlpManager,
    log_level: str,
) -> None:
    log_level_int = getattr(logging, log_level.upper(), logging.WARNING)
    logging.basicConfig(level=log_level_int, format="%(asctime)s - %(levelname)s - %(message)s")

    log("🚀 Запускаю бота vk-to-tg...")
    try:
        while not shutdown_event.is_set():
            log(f"🔍 {datetime.now().strftime('%H:%M:%S %Y-%m-%d')} | Начинаю новый цикл проверки...", padding_top=1)
            for binding in settings.bindings:
                vk_config = binding.vk
                telegram_config = binding.telegram
                domain = vk_config.domain
                post_count = vk_config.post_count
                post_source = vk_config.post_source
                channel_ids = telegram_config.channel_ids

                last_known_id = await get_last_post_id(domain)
                log(f"📄 Проверяю группу {domain}...", indent=1, padding_top=1)

                wall_posts = await vk_manager.get_vk_wall(domain, post_count, post_source)
                new_posts = [p for p in wall_posts if p.id > last_known_id]

                if new_posts:
                    log(f"✅ Найдено {len(new_posts)} новых постов в {domain}.", indent=2)
                    for post in sorted(new_posts, key=lambda p: p.id):
                        await process_post(post, domain, channel_ids, shutdown_event, ytdlp_manager, tg_manager)
                        await set_last_post_id(domain, post.id)
                        last_known_id = post.id

            log(f"🏁 Цикл завершен. Пауза {settings.app.wait_time_seconds} секунд...", padding_top=1)

            await asyncio.sleep(settings.app.wait_time_seconds)

    except asyncio.CancelledError:
        log("🛑 Получен сигнал на завершение — выходим из run_app.", padding_top=1)


async def process_post(
    post: Post,
    domain: str,
    channel_ids: list[str],
    shutdown_event: asyncio.Event,
    ytdlp_manager: YtDlpManager,
    tg_manager: TelegramClientManager,
) -> None:
    log(f"📄 Обрабатываю пост ID: {post.id} из {domain}...", indent=2, padding_top=1)
    post_text: str = post.text or ""
    video_urls: list[str] = []

    if post.attachments:
        for attachment in post.attachments:
            if attachment.type == "video" and attachment.video:
                video = attachment.video
                access_key_part = f"?access_key={video.access_key}" if video.access_key else ""
                video_url = f"https://vk.com/video{video.owner_id}_{video.id}{access_key_part}"
                video_urls.append(video_url)

    if video_urls:
        log(f"📹 Найдено {len(video_urls)} видео в посте.", indent=3)
        downloaded_files: list[Path] = []
        for video_url in video_urls:
            log(f"📹 Скачиваю видео: {video_url}", indent=4)
            try:
                downloaded_file_path = await ytdlp_manager.download_video(video_url)
                if downloaded_file_path:
                    downloaded_files.append(downloaded_file_path)
            except asyncio.CancelledError:
                log("⏹️ Загрузка прервана пользователем.", indent=4)
                raise

            if shutdown_event.is_set():
                log("⏹️ Остановка запрошена — прерываю обработку поста.", indent=4)
                raise asyncio.CancelledError()

        if downloaded_files:
            for channel_id in channel_ids:
                try:
                    await tg_manager.send_media(channel_id, downloaded_files, post_text)
                except asyncio.CancelledError:
                    log("⏹️ Отправка прервана пользователем.", indent=4, padding_top=1)
                    raise

            log("🗑️ Удаляю временные файлы...", indent=4, padding_top=1)
            for file_path in downloaded_files:
                try:
                    await asyncio.to_thread(os.remove, file_path)
                    log(f"✅ Файл {file_path} удален.", indent=4)
                except FileNotFoundError:
                    log(f"⚠️ Файл {file_path} уже удалён или не найден.", indent=4)
                except Exception as e:
                    log(f"❌ Ошибка удаления файла {file_path}: {e}", indent=4)
    else:
        log("🤷‍♂️ Видео в посте не найдено, пропускаю.", indent=3)
