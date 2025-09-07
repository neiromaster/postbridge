import asyncio
import sys
import time
from pathlib import Path

from pyrogram.client import Client
from pyrogram.errors import ChannelPrivate, FloodWait, PeerIdInvalid, RPCError
from pyrogram.types import InputMedia, InputMediaPhoto, InputMediaVideo, Message

from ..config import settings
from ..exceptions import GracefulShutdown


class _Progress:
    """Progress bar for sending files to Telegram."""

    def __init__(self) -> None:
        self.start_time = time.time()

    def __call__(self, current: int, total: int) -> None:
        now = time.time()
        elapsed = now - self.start_time
        speed_bps = current / elapsed if elapsed > 0 else 0.0
        speed_mbps = speed_bps * 8 / (1024 * 1024)
        percent = (current / total) * 100 if total else 0.0
        current_mb = current / (1024 * 1024)
        total_mb = total / (1024 * 1024) if total else 0.0
        bar_length = 15
        filled_length = int(bar_length * current // total) if total else 0
        bar = "█" * filled_length + "-" * (bar_length - filled_length)
        sys.stdout.write(f"\r[{bar}] {percent:5.1f}% | {current_mb:.1f} / {total_mb:.1f} МБ | {speed_mbps:.1f} Мбит/с ")
        sys.stdout.flush()


class TelegramClientManager:
    """Manages Kurigram client and handles sending media to Telegram channels."""

    def __init__(self, shutdown_event: asyncio.Event) -> None:
        """Initialize the manager with a shutdown event."""
        self.shutdown_event = shutdown_event
        self.app: Client | None = None

    async def start(self) -> None:
        """Start the Telegram client session."""
        try:
            self.app = Client(
                settings.app.session_name,
                api_id=settings.telegram_api_id,
                api_hash=settings.telegram_api_hash,
            )
            await self.app.start()
            print("🚀 Telegram Client запущен")
        except asyncio.CancelledError as e:
            print("⏹️ Запуск Telegram клиента прерван пользователем.")
            raise GracefulShutdown() from e

    async def stop(self) -> None:
        """Stop the Telegram client session."""
        if self.app:
            await self.app.stop()
            print("🛑 Telegram Client остановлен")

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
            print(f"⚠️ Формат {file_path} не поддерживается.")

    async def _send_single_video(self, channel: int | str, file_path: Path, caption: str, max_retries: int) -> None:
        attempt = 0
        while attempt < max_retries:
            try:
                print(f"✈️ Отправка видео (попытка {attempt + 1}/{max_retries})...")
                assert self.app is not None
                await self.app.send_video(  # type: ignore[reportUnknownMemberType]
                    chat_id=channel,
                    video=str(file_path),
                    caption=caption,
                    progress=_Progress(),
                )
                print(f"\n✅ Видео '{file_path}' отправлено.")
                return
            except FloodWait as e:
                await self._handle_floodwait(e)
            except (PeerIdInvalid, ChannelPrivate):
                print(f"⚠️ Канал '{channel}' недоступен.")
                return
            except RPCError as e:
                print(f"❌ Ошибка API: {e}")
                await self._sleep_cancelable(5)
            except Exception as e:
                print(f"❌ Неизвестная ошибка: {e}")
                await self._sleep_cancelable(3)
            attempt += 1

    async def _send_single_photo(self, channel: int | str, file_path: Path, caption: str, max_retries: int) -> None:
        attempt = 0
        while attempt < max_retries:
            try:
                print(f"✈️ Отправка фото (попытка {attempt + 1}/{max_retries})...")
                assert self.app is not None
                await self.app.send_photo(  # type: ignore[reportUnknownMemberType]
                    chat_id=channel,
                    photo=str(file_path),
                    caption=caption,
                    progress=_Progress(),
                )
                print(f"\n✅ Фото '{file_path}' отправлено.")
                return
            except FloodWait as e:
                await self._handle_floodwait(e)
            except (PeerIdInvalid, ChannelPrivate):
                print(f"⚠️ Канал '{channel}' недоступен или приватный. Пропускаю.")
                return

            except RPCError as e:
                print(f"❌ Ошибка Telegram API: {type(e).__name__} — {e}")
                await self._sleep_cancelable(5)

            except Exception as e:
                print(f"❌ Неизвестная ошибка отправки: {e}")
                await self._sleep_cancelable(3)

            attempt += 1

    async def _send_album_via_saved(
        self, channel: int | str, files: list[Path], caption: str, max_retries: int
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
                    print(f"⬆️ Загрузка {i + 1}/{len(files)} в Избранное: {file_path.name}")
                    msg: Message | None = None
                    if suffix in [".jpg", ".jpeg", ".png", ".webp"]:
                        msg = await self.app.send_photo(  # type: ignore[reportUnknownMemberType]
                            chat_id="me",
                            photo=str(file_path),
                            caption=caption if i == 0 else "",
                            progress=_Progress(),
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
                            progress=_Progress(),
                        )
                        if msg and msg.video:
                            uploaded_media.append(
                                InputMediaVideo(media=msg.video.file_id, caption=caption if i == 0 else "")
                            )
                    else:
                        print(f"⚠️ Формат {file_path} не поддерживается для альбомов.")

                    if msg and msg.id:
                        temp_message_ids.append(msg.id)
                    break

                except FloodWait as e:
                    await self._handle_floodwait(e)
                except RPCError as e:
                    print(f"❌ Ошибка Telegram API: {type(e).__name__} — {e}")
                    await self._sleep_cancelable(5)
                except Exception as e:
                    print(f"❌ Неизвестная ошибка отправки: {e}")
                    await self._sleep_cancelable(3)
                attempt += 1

        if len(uploaded_media) > 1:
            print("📦 Формирование альбома...")
            await self.app.send_media_group(chat_id=channel, media=uploaded_media)  # type: ignore[reportGeneralTypeIssues]
            print("✅ Альбом отправлен в канал.")

        if temp_message_ids:
            try:
                await self.app.delete_messages(chat_id="me", message_ids=temp_message_ids)
                print("🧹 Временные сообщения из Избранного удалены.")
            except Exception as e:
                print(f"⚠️ Не удалось удалить временные сообщения: {e}")

    async def _handle_floodwait(self, e: FloodWait) -> None:
        wait_time = e.value if isinstance(e.value, int) else 60
        print(f"⏳ FloodWait: жду {wait_time + 1} секунд...")
        await self._sleep_cancelable(wait_time + 1)

    async def _sleep_cancelable(self, seconds: int) -> None:
        remaining = float(seconds)
        step = 0.25
        while remaining > 0:
            if self.shutdown_event.is_set():
                raise GracefulShutdown()
            await asyncio.sleep(step)
            remaining -= step
