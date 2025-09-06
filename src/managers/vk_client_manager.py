import asyncio
from typing import Any

import httpx

from ..cleaner import normalize_links
from ..config import settings
from ..dto import Post, WallGetResponse
from ..exceptions import GracefulShutdown


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
            print("🚀 VK Client запущен")
        except asyncio.CancelledError as e:
            print("⏹️ Запуск VK клиента прерван пользователем.")
            raise GracefulShutdown() from e

    async def stop(self) -> None:
        if self.client:
            await self.client.aclose()
        print("🛑 VK Client остановлен")

    async def get_vk_wall(self, domain: str, post_count: int, post_source: str) -> list[Post]:
        """Requests posts from a VK wall (or Donut) with retry and cancellation on shutdown_event."""
        if self.shutdown_event.is_set():
            raise GracefulShutdown()

        assert self.client is not None, "VKClientManager не запущен"

        params: dict[str, Any] = {
            "domain": domain,
            "count": post_count,
            "access_token": settings.vk_service_token,
            "v": "5.199",
        }
        if post_source == "donut":
            params["filter"] = "donut"
            print(f"🔍 Собираю посты из VK Donut: {domain}...")
        else:
            print(f"🔍 Собираю посты со стены: {domain}...")

        delay = 2
        for attempt in range(3):
            if self.shutdown_event.is_set():
                raise GracefulShutdown()

            try:
                response = await self.client.get("https://api.vk.com/method/wall.get", params=params)
                if self.shutdown_event.is_set():
                    raise GracefulShutdown()

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

            except asyncio.CancelledError as e:
                print("⏹️ Запрос к VK API прерван пользователем.")
                raise GracefulShutdown() from e

            except Exception as e:
                if attempt < 2:
                    print(f"❌ Ошибка VK API: {e}. Повтор через {delay} c...")
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
                raise GracefulShutdown()
            await asyncio.sleep(step)
            remaining -= step
