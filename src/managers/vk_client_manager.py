import asyncio
from pathlib import Path
from typing import Any

import anyio
import httpx
from pydantic import HttpUrl

from ..cleaner import normalize_links
from ..config import settings
from ..dto import Post, WallGetResponse
from ..printer import log


class VKClientManager:
    """Manages the HTTP client for VK and provides methods for working with the API."""

    def __init__(self, shutdown_event: asyncio.Event) -> None:
        self.shutdown_event = shutdown_event
        self.client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        try:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(10.0, connect=5.0), http2=True, headers={"User-Agent": "PostBridgeBot/1.0"}
            )
            log("🚀 VK Client запущен", indent=1)
        except asyncio.CancelledError:
            log("⏹️ Запуск VK клиента прерван пользователем.", indent=1)
            raise

    async def stop(self) -> None:
        if self.client:
            await self.client.aclose()
        log("🛑 VK Client остановлен", indent=1)

    async def download_photo(self, url: HttpUrl) -> Path | None:
        """Downloads a photo from a given URL and saves it to the downloads directory."""
        if self.shutdown_event.is_set():
            raise asyncio.CancelledError()
        assert self.client is not None, "VKClientManager is not started"

        if not url.path:
            log(f"❌ Не удалось получить путь из URL: {url}", indent=4)
            return None
        file_name = Path(url.path).name
        save_path = Path("downloads") / file_name
        save_path.parent.mkdir(exist_ok=True)

        try:
            async with self.client.stream("GET", str(url)) as response:
                response.raise_for_status()
                async with await anyio.open_file(save_path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        if self.shutdown_event.is_set():
                            raise asyncio.CancelledError()
                        await f.write(chunk)
            log(f"✅ Фотография сохранена: {save_path}", indent=4)
            return save_path
        except asyncio.CancelledError:
            log("⏹️ Загрузка фотографии прервана.", indent=4)
            if save_path.exists():
                save_path.unlink()
            raise
        except Exception as e:
            log(f"❌ Не удалось скачать фотографию: {e}", indent=4)
            if save_path.exists():
                save_path.unlink()
            return None

    async def get_vk_wall(self, domain: str, post_count: int, post_source: str) -> list[Post]:
        """Requests posts from a VK wall (or Donut) with retry and cancellation on shutdown_event."""
        if self.shutdown_event.is_set():
            raise asyncio.CancelledError()

        assert self.client is not None, "VKClientManager не запущен"

        params: dict[str, Any] = {
            "domain": domain,
            "count": post_count,
            "access_token": settings.vk_service_token,
            "v": "5.199",
        }
        if post_source == "donut":
            params["filter"] = "donut"
            log(f"🔍 Собираю посты из VK Donut: {domain}...", indent=2)
        else:
            log(f"🔍 Собираю посты со стены: {domain}...", indent=2)

        delay = 2
        for attempt in range(3):
            if self.shutdown_event.is_set():
                raise asyncio.CancelledError()

            try:
                response = await self.client.get("https://api.vk.com/method/wall.get", params=params)
                if self.shutdown_event.is_set():
                    raise asyncio.CancelledError()

                response.raise_for_status()
                data = response.json()
                if "error" in data:
                    raise RuntimeError(f"VK API Error: {data['error']['error_msg']}")
                raw = data["response"]
                posts = WallGetResponse.model_validate(raw).items
                for post in posts:
                    if post.text:
                        post.text = normalize_links(post.text)
                return posts

            except asyncio.CancelledError:
                log("⏹️ Запрос к VK API прерван пользователем.", indent=3)
                raise

            except Exception as e:
                if attempt < 2:
                    log(f"❌ Ошибка VK API: {e}. Повтор через {delay} c...", indent=3)
                    await self._sleep_cancelable(delay)
                    delay *= 2
                else:
                    raise
        return []

    async def _sleep_cancelable(self, seconds: int) -> None:
        """A sleep that is interrupted by a shutdown event."""
        remaining = float(seconds)
        step = 0.25
        while remaining > 0:
            if self.shutdown_event.is_set():
                raise asyncio.CancelledError()
            await asyncio.sleep(step)
            remaining -= step
