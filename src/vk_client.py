import os
import re
import vk_api
from dotenv import load_dotenv

load_dotenv()


def clean_post_text(text):
    """Cleans the post text by removing VK-style links."""
    return re.sub(r"\[[^\]|]*\|([^\]]*)\]", r"\1", text)


def get_vk_wall():
    """Get posts from a VK wall."""
    token = os.getenv("VK_SERVICE_TOKEN")
    domain = os.getenv("VK_DOMAIN")
    if not token or not domain:
        raise ValueError("VK_SERVICE_TOKEN and VK_DOMAIN must be set in .env file")

    print(f"Fetching posts from VK wall: {domain}...")
    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()
    response = vk.wall.get(domain=domain, count=10)
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
