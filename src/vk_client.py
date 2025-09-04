from typing import Any, Dict, List

import vk_api

from .cleaner import normalize_links
from .config import settings
from .dto import Post, WallGetResponse


def get_vk_wall(domain: str, post_count: int, post_source: str) -> List[Post]:
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

    vk_session = vk_api.VkApi(token=settings.vk_service_token)
    vk = vk_session.get_api()
    response = vk.wall.get(**params)

    posts = WallGetResponse.model_validate(response).items
    for post in posts:
        if post.text:
            post.text = normalize_links(post.text)

    return posts
