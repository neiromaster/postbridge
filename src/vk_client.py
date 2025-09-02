import re
import vk_api
from .config import VK_SERVICE_TOKEN, VK_DOMAIN, VK_POST_COUNT, VK_POST_SOURCE


def clean_post_text(text):
    """
    Cleans the post text by converting VK-style links to Markdown format.
    - [link|text] -> [text](link) for valid URLs.
    - [club123|text] -> [text](https://vk.com/club123) for internal VK links.
    - Other [..|..] constructs are cleaned to just the text part.
    """

    def replacer(match):
        link = match.group(1)
        text = match.group(2)

        if link.startswith("http://") or link.startswith("https://"):
            return f"[{text}]({link})"
        elif link.startswith("club") or link.startswith("id"):
            return f"[{text}](https://vk.com/{link})"
        else:
            return text

    return re.sub(r"\[([^\]|]+)\|([^\]]+)\]", replacer, text)


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
            post["text"] = clean_post_text(post["text"])

    return posts


if __name__ == "__main__":
    wall_posts = get_vk_wall()
    for post in wall_posts:
        print(post)
