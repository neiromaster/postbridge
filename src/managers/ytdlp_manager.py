from __future__ import annotations

import asyncio
import subprocess
import sys
from multiprocessing import Process, Queue
from pathlib import Path
from typing import Any, cast

import psutil
import yt_dlp

from ..config import settings
from ..exceptions import GracefulShutdown

BROWSER_EXECUTABLES = (
    {
        "firefox": "firefox.exe",
        "chrome": "chrome.exe",
        "edge": "msedge.exe",
    }
    if sys.platform == "win32"
    else {
        "firefox": "firefox",
        "chrome": "google-chrome",
        "edge": "microsoft-edge",
    }
)


def _ytdlp_worker(url: str, opts: dict[str, Any], out_q: Queue[str]) -> None:
    """Worker process: downloads a video and sends the file path through a queue."""
    try:
        with yt_dlp.YoutubeDL(cast(Any, opts)) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)
            out_q.put(downloaded_file)
    except BaseException:
        pass


class YtDlpManager:
    """Handles video downloading via yt-dlp in a separate process."""

    def __init__(self, shutdown_event: asyncio.Event) -> None:
        """Initialize the manager with a shutdown event."""
        self.shutdown_event = shutdown_event
        self._active_proc: Process | None = None

    async def start(self) -> None:
        """Prepare the manager for downloading."""
        print("🚀 YtDlp Manager готов к работе")

    async def stop(self) -> None:
        """Terminate any active download process."""
        await self._terminate_active()
        print("🛑 YtDlp Manager остановлен")

    async def _terminate_active(self) -> None:
        proc = self._active_proc
        if proc and proc.is_alive():
            print("🛑 Прерываю активную загрузку yt-dlp...")
            proc.terminate()
            for _ in range(20):
                if not proc.is_alive():
                    break
                await asyncio.sleep(0.1)
            if proc.is_alive():
                proc.kill()
            proc.join(timeout=1.0)
        self._active_proc = None

    async def restart_browser(self) -> None:
        """Restarts the browser to update cookies."""
        browser_name = settings.downloader.browser
        executable = BROWSER_EXECUTABLES.get(browser_name)
        if not executable:
            print(f"⚠️ Браузер {browser_name} не поддерживается для перезапуска.")
            return

        print(f"🔄 Перезапускаю {browser_name} для обновления cookie...")

        for proc in psutil.process_iter(["name"]):  # type: ignore [reportUnknownMemberType, reportUnknownArgumentType])
            if proc.info["name"] == executable:
                await asyncio.to_thread(proc.kill)
                await asyncio.to_thread(proc.wait)

        await asyncio.to_thread(subprocess.Popen, [executable])
        await asyncio.sleep(settings.downloader.browser_restart_wait_seconds)

        for proc in psutil.process_iter(["name"]):  # type: ignore [reportUnknownMemberType, reportUnknownArgumentType])
            if proc.info["name"] == executable:
                await asyncio.to_thread(proc.kill)
                await asyncio.to_thread(proc.wait)
                break

        print("✅ Перезапуск завершен.")

    async def download_video(self, video_url: str) -> Path | None:
        """
        Download a video via yt-dlp in a separate process.
        Guaranteed to stop on shutdown or cancellation.
        """
        if self.shutdown_event.is_set():
            raise GracefulShutdown()

        out_dir = Path(settings.downloader.output_path)
        out_dir.mkdir(parents=True, exist_ok=True)

        ydl_opts: dict[str, Any] = dict(settings.downloader.yt_dlp_opts)
        ydl_opts.update(
            {
                "outtmpl": str(out_dir / "%(id)s.%(ext)s"),
                "cookiesfrombrowser": (settings.downloader.browser,),
                "quiet": True,
                "no_warnings": True,
                "verbose": False,
            }
        )

        retries = settings.downloader.retries.count
        base_delay = settings.downloader.retries.delay_seconds

        for attempt in range(retries):
            if self.shutdown_event.is_set():
                print("⏹️ Загрузка отменена пользователем.")
                raise GracefulShutdown()

            print(f"📥 Скачиваю видео (попытка {attempt + 1}/{retries})...")
            out_q: Queue[str] = Queue()
            proc = Process(target=_ytdlp_worker, args=(video_url, ydl_opts, out_q), daemon=True)
            proc.start()
            self._active_proc = proc

            try:
                downloaded_file = await self._wait_for_result_or_shutdown(proc, out_q)
                if downloaded_file:
                    print(f"✅ Видео скачано: {downloaded_file}")
                    return Path(downloaded_file)
                else:
                    raise GracefulShutdown()
            except asyncio.CancelledError as e:
                await self._terminate_active()
                print("⏹️ Загрузка отменена (CancelledError).")
                raise GracefulShutdown() from e
            except Exception as e:
                print(f"❌ Ошибка скачивания: {e}")

                if "This video is only available for registered users" in str(e) and attempt < retries - 1:
                    await self.restart_browser()
                    continue

                await self._terminate_active()
                if attempt < retries - 1 and not self.shutdown_event.is_set():
                    current_delay = base_delay * (2**attempt)
                    print(f"⏳ Пауза {current_delay} секунд перед следующей попыткой...")
                    await self._sleep_cancelable(current_delay)

        print(f"❌ Не удалось скачать видео после {retries} попыток.")
        return None

    async def _wait_for_result_or_shutdown(self, proc: Process, out_q: Queue[str]) -> str | None:
        while proc.is_alive():
            if self.shutdown_event.is_set():
                await self._terminate_active()
                return None
            try:
                return out_q.get_nowait()
            except Exception:
                pass
            await asyncio.sleep(0.15)

        try:
            return out_q.get_nowait()
        except Exception:
            return None

    async def _sleep_cancelable(self, seconds: int) -> None:
        remaining = float(seconds)
        step = 0.25
        while remaining > 0 and not self.shutdown_event.is_set():
            await asyncio.sleep(step)
            remaining -= step
