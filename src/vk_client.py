import re
import vk_api
from .config import VK_SERVICE_TOKEN, VK_DOMAIN, VK_POST_COUNT


def clean_post_text(text):
    """Cleans the post text by removing VK-style links."""
    return re.sub(r"\[[^\]|]*\|([^\]]*)\]", r"\1", text)


def get_vk_wall():
    """Get posts from a VK wall."""

    print(f"Fetching posts from VK wall: {VK_DOMAIN}...")
    vk_session = vk_api.VkApi(token=VK_SERVICE_TOKEN)
    vk = vk_session.get_api()
    response = vk.wall.get(domain=VK_DOMAIN, count=VK_POST_COUNT)
    print(f"Found {len(response['items'])} posts.")

    posts = response["items"]
    for post in posts:
        if "text" in post:
            post["text"] = clean_post_text(post["text"])

    return posts


if __name__ == "__main__":
    wall_posts = get_vk_wall()
    for post in wall_posts:
        print(post)
