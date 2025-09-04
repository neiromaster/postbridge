from typing import Any, Dict, List

import httpx

from .cleaner import normalize_links
from .config import settings
from .dto import Post, WallGetResponse


async def get_vk_wall(domain: str, post_count: int, post_source: str) -> List[Post]:
    """Get posts from a VK wall."""

    params: Dict[str, Any] = {
        "domain": domain,
        "count": post_count,
    }
    if post_source == "donut":
        params["filter"] = "donut"
        print(f"🔍 Собираю посты из VK Donut: {domain}...")
    else:
        print(f"🔍 Собираю посты со стены: {domain}...")

    VK_API_BASE_URL = "https://api.vk.com/method/"
    VK_API_VERSION = "5.199"

    params["access_token"] = settings.vk_service_token
    params["v"] = VK_API_VERSION

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{VK_API_BASE_URL}wall.get", params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        response_data = response.json()

    if "error" in response_data:
        raise Exception(f"VK API Error: {response_data['error']['error_msg']}")

    response = response_data["response"]

    posts = WallGetResponse.model_validate(response).items
    for post in posts:
        if post.text:
            post.text = normalize_links(post.text)

    return posts
