import asyncio
import sys
import time
from pathlib import Path

from pyrogram.client import Client
from pyrogram.errors import ChannelPrivate, FloodWait, PeerIdInvalid, RPCError

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

        sys.stdout.write(f"\r[{bar}] {percent:5.1f}% | {current_mb:.1f} / {total_mb:.1f}МБ | {speed_mbps:.1f}Мбит/с  ")
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

    async def send_video(
        self,
        channel: int | str,
        file_path: Path,
        caption: str,
        max_retries: int = 3,
    ) -> None:
        """
        Send a video file to a Telegram channel with retry, FloodWait handling,
        and graceful cancellation support.
        """
        assert self.app is not None, "TelegramClientManager is not started"

        attempt = 0
        while attempt < max_retries:
            try:
                print(f"✈️ Отправка в Telegram (попытка {attempt + 1}/{max_retries})...")
                await self.app.send_video(  # type: ignore[reportUnknownMemberType]
                    chat_id=channel,
                    video=str(file_path),
                    caption=caption,
                    progress=_Progress(),
                )
                sys.stdout.write("\n")
                print(f"✅ Файл '{file_path}' отправлен в '{channel}'.")
                return

            except asyncio.CancelledError as e:
                print("⏹️ Отправка видео прервана пользователем.")
                raise GracefulShutdown() from e

            except FloodWait as e:
                wait_time = e.value
                if isinstance(wait_time, int):
                    print(f"⏳ FloodWait: жду {wait_time + 1} секунд...")
                    await self._sleep_cancelable(wait_time + 1)
                else:
                    print(f"⏳ FloodWait: непредвиденное значение {wait_time}, жду 60 секунд...")
                    await self._sleep_cancelable(60)

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

        if attempt >= max_retries:
            print(f"⚠️ Не удалось отправить файл '{file_path}' в канал '{channel}' после {max_retries} попыток.")

    async def _sleep_cancelable(self, seconds: int) -> None:
        """A sleep that can be interrupted by a shutdown_event."""
        remaining = float(seconds)
        step = 0.25
        while remaining > 0:
            if self.shutdown_event.is_set():
                raise GracefulShutdown()
            await asyncio.sleep(step)
            remaining -= step
