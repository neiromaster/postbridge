import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pyrogram.client import Client
from pyrogram.errors import ChannelPrivate, FloodWait, PeerIdInvalid, RPCError
from pyrogram.types import InputMedia, InputMediaPhoto, InputMediaVideo, Message
from tqdm import tqdm

from ..config import settings
from ..printer import log


class TelegramClientManager:
    """Manages Kurigram client and handles sending media to Telegram channels."""

    def __init__(self, shutdown_event: asyncio.Event) -> None:
        """Initialize the manager with a shutdown event."""
        self.shutdown_event = shutdown_event
        self.app: Client | None = None
        self.pbar: tqdm[Any] | None = None

    def _create_progress_callback(self, indent: int) -> Callable[[int, int], None]:
        def _progress_hook(current: int, total: int) -> None:
            current_mb = current / (1024 * 1024)
            total_mb = total / (1024 * 1024) if total else 0

            if self.pbar is None:
                self.pbar = tqdm(
                    total=total_mb,
                    unit="MB",
                    unit_scale=False,
                    desc="  " * indent + "🚀 ",
                    ncols=80,
                    bar_format="{desc}{bar}| {n:.0f} / {total:.0f} {unit} | {elapsed} < {remaining} | {rate_fmt}{postfix}",  # noqa: E501
                )

            self.pbar.update(current_mb - self.pbar.n)

            if current >= total:
                self.pbar.close()
                self.pbar = None

        return _progress_hook

    async def start(self) -> None:
        """Start the Telegram client session."""
        try:
            self.app = Client(
                settings.app.session_name,
                api_id=settings.telegram_api_id,
                api_hash=settings.telegram_api_hash,
            )
            await self.app.start()
            log("🚀 Telegram Client запущен", indent=1)
        except asyncio.CancelledError:
            log("⏹️ Запуск Telegram клиента прерван пользователем.", indent=1)
            raise

    async def stop(self) -> None:
        """Stop the Telegram client session."""
        if self.app and self.app.is_connected:
            await self.app.stop()
            log("🛑 Telegram Client остановлен", indent=1)

    async def send_media(self, channel: int | str, files: list[Path], caption: str = "", max_retries: int = 3) -> None:
        """
        Universal Sending:
        - 1 file → directly to the progress channel
        - a few → through Favorites with progress, then the album to the channel
        """
        assert self.app is not None, "TelegramClientManager is not started"

        files = sorted(files, key=lambda p: p.name)

        if len(files) == 1:
            await self._send_single(channel, files[0], caption, max_retries)
        else:
            await self._send_album_via_saved(channel, files, caption, max_retries)

    async def _send_single(self, channel: int | str, file_path: Path, caption: str, max_retries: int) -> None:
        suffix = file_path.suffix.lower()
        if suffix in [".jpg", ".jpeg", ".png", ".webp"]:
            await self._send_single_photo(channel, file_path, caption, max_retries)
        elif suffix in [".mp4", ".mov", ".mkv"]:
            await self._send_single_video(channel, file_path, caption, max_retries)
        else:
            log(f"⚠️ Формат {file_path} не поддерживается.", indent=4)

    async def _send_single_video(self, channel: int | str, file_path: Path, caption: str, max_retries: int) -> None:
        attempt = 0
        while attempt < max_retries:
            try:
                log(f"✈️ Отправка видео (попытка {attempt + 1}/{max_retries})...", indent=4, padding_top=1)
                assert self.app is not None
                await self.app.send_video(  # type: ignore[reportUnknownMemberType]
                    chat_id=channel,
                    video=str(file_path),
                    caption=caption,
                    progress=self._create_progress_callback(indent=4),
                )
                log(f"✅ Видео '{file_path}' отправлено.", indent=4, padding_top=1)
                return
            except FloodWait as e:
                await self._handle_floodwait(e)
            except (PeerIdInvalid, ChannelPrivate):
                log(f"⚠️ Канал '{channel}' недоступен.", indent=4)
                return
            except RPCError as e:
                log(f"❌ Ошибка API: {e}", indent=4)
                await self._sleep_cancelable(5)
            except Exception as e:
                log(f"❌ Неизвестная ошибка: {e}", indent=4)
                await self._sleep_cancelable(3)
            attempt += 1

    async def _send_single_photo(self, channel: int | str, file_path: Path, caption: str, max_retries: int) -> None:
        attempt = 0
        while attempt < max_retries:
            try:
                log(f"✈️ Отправка фото (попытка {attempt + 1}/{max_retries})...", indent=4)
                assert self.app is not None
                await self.app.send_photo(  # type: ignore[reportUnknownMemberType]
                    chat_id=channel,
                    photo=str(file_path),
                    caption=caption,
                    progress=self._create_progress_callback(indent=4),
                )
                log(f"✅ Фото '{file_path}' отправлено.", indent=4, padding_top=1)
                return
            except FloodWait as e:
                await self._handle_floodwait(e)
            except (PeerIdInvalid, ChannelPrivate):
                log(f"⚠️ Канал '{channel}' недоступен или приватный. Пропускаю.", indent=4)
                return

            except RPCError as e:
                log(f"❌ Ошибка Telegram API: {type(e).__name__} — {e}", indent=4)
                await self._sleep_cancelable(5)

            except Exception as e:
                log(f"❌ Неизвестная ошибка отправки: {e}", indent=4)
                await self._sleep_cancelable(3)

            attempt += 1

    async def _send_album_via_saved(
        self,
        channel: int | str,
        files: list[Path],
        caption: str,
        max_retries: int,
    ) -> None:
        """
        Uploads the media to Favorites with progress, then sends the album to the channel.
        """
        assert self.app is not None
        uploaded_media: list[InputMedia] = []
        temp_message_ids: list[int] = []

        for i, file_path in enumerate(files):
            suffix = file_path.suffix.lower()
            attempt = 0
            while attempt < max_retries:
                try:
                    log(f"⬆️ Загрузка {i + 1}/{len(files)} в Избранное: {file_path.name}", indent=4)
                    msg: Message | None = None
                    if suffix in [".jpg", ".jpeg", ".png", ".webp"]:
                        msg = await self.app.send_photo(  # type: ignore[reportUnknownMemberType]
                            chat_id="me",
                            photo=str(file_path),
                            caption=caption if i == 0 else "",
                            progress=self._create_progress_callback(indent=4),
                        )
                        if msg and msg.photo:
                            uploaded_media.append(
                                InputMediaPhoto(media=msg.photo.file_id, caption=caption if i == 0 else "")
                            )

                    elif suffix in [".mp4", ".mov", ".mkv"]:
                        msg = await self.app.send_video(  # type: ignore[reportUnknownMemberType]
                            chat_id="me",
                            video=str(file_path),
                            caption=caption if i == 0 else "",
                            progress=self._create_progress_callback(indent=4),
                        )
                        if msg and msg.video:
                            uploaded_media.append(
                                InputMediaVideo(media=msg.video.file_id, caption=caption if i == 0 else "")
                            )
                    else:
                        log(f"⚠️ Формат {file_path} не поддерживается для альбомов.", indent=4)

                    if msg and msg.id:
                        temp_message_ids.append(msg.id)
                    break

                except FloodWait as e:
                    await self._handle_floodwait(e)
                except RPCError as e:
                    log(f"❌ Ошибка Telegram API: {type(e).__name__} — {e}", indent=4)
                    await self._sleep_cancelable(5)
                except Exception as e:
                    log(f"❌ Неизвестная ошибка отправки: {e}", indent=4)
                    await self._sleep_cancelable(3)
                attempt += 1

        if len(uploaded_media) > 1:
            log("📦 Формирование альбома...", indent=4)
            await self.app.send_media_group(chat_id=channel, media=uploaded_media)  # type: ignore[reportGeneralTypeIssues]
            log("✅ Альбом отправлен в канал.", indent=4)

        if temp_message_ids:
            try:
                await self.app.delete_messages(chat_id="me", message_ids=temp_message_ids)
                log("🧹 Временные сообщения из Избранного удалены.", indent=4)
            except Exception as e:
                log(f"⚠️ Не удалось удалить временные сообщения: {e}", indent=4)

    async def _handle_floodwait(self, e: FloodWait) -> None:
        wait_time = e.value if isinstance(e.value, int) else 60
        log(f"⏳ FloodWait: жду {wait_time + 1} секунд...", indent=4)
        await self._sleep_cancelable(wait_time + 1)

    async def _sleep_cancelable(self, seconds: int) -> None:
        remaining = float(seconds)
        step = 0.25
        while remaining > 0:
            if self.shutdown_event.is_set():
                raise asyncio.CancelledError()
            await asyncio.sleep(step)
            remaining -= step
