import vk_api

from .cleaner import normalize_links
from .config import VK_DOMAIN, VK_POST_COUNT, VK_POST_SOURCE, VK_SERVICE_TOKEN


def get_vk_wall():
    """Get posts from a VK wall."""

    params = {
        "domain": VK_DOMAIN,
        "count": VK_POST_COUNT,
    }
    if VK_POST_SOURCE == "donut":
        params["filter"] = "donut"
        print(f"🔍 Собираю посты из VK Donut: {VK_DOMAIN}...")
    else:
        print(f"🔍 Собираю посты со стены: {VK_DOMAIN}...")

    vk_session = vk_api.VkApi(token=VK_SERVICE_TOKEN)
    vk = vk_session.get_api()
    response = vk.wall.get(**params)

    posts = response["items"]
    for post in posts:
        if "text" in post:
            post["text"] = normalize_links(post["text"])

    return posts


if __name__ == "__main__":
    wall_posts = get_vk_wall()
    for post in wall_posts:
        print(post)
