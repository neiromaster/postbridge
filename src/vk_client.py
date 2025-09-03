import vk_api

from .cleaner import normalize_links
from .config import VK_SERVICE_TOKEN


def get_vk_wall(domain, post_count, post_source):
    """Get posts from a VK wall."""

    params = {
        "domain": domain,
        "count": post_count,
    }
    if post_source == "donut":
        params["filter"] = "donut"
        print(f"🔍 Собираю посты из VK Donut: {domain}...")
    else:
        print(f"🔍 Собираю посты со стены: {domain}...")

    vk_session = vk_api.VkApi(token=VK_SERVICE_TOKEN)
    vk = vk_session.get_api()
    response = vk.wall.get(**params)

    posts = response["items"]
    for post in posts:
        if "text" in post:
            post["text"] = normalize_links(post["text"])

    return posts
