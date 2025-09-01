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

    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()
    response = vk.wall.get(domain=domain, count=10)
    return response["items"]
