import os
import vk_api
from dotenv import load_dotenv

load_dotenv()


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
    return response["items"]


if __name__ == "__main__":
    # Example usage
    wall_posts = get_vk_wall()
    for post in wall_posts:
        print(post)

