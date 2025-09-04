import asyncio
import os

import aiofiles
import yaml

from .config import settings
from .dto import State


async def _load_state() -> State:
    """Loads the state from the YAML file."""
    if not os.path.exists(settings.app.state_file):
        return State(root={})
    try:
        async with aiofiles.open(settings.app.state_file, "r") as f:
            content = await f.read()
            state_data = await asyncio.to_thread(yaml.safe_load, content)
            return State(root=state_data) if state_data else State(root={})
    except (yaml.YAMLError, FileNotFoundError):
        return State(root={})


async def _save_state(state: State) -> None:
    """Saves the state to the YAML file."""
    async with aiofiles.open(settings.app.state_file, "w") as f:
        content = await asyncio.to_thread(yaml.dump, state.model_dump(mode="json"), indent=4)
        await f.write(content)


async def get_last_post_id(domain: str) -> int:
    """Reads the last processed post ID for a specific domain from the state file."""
    print(f"\n💾 Читаю ID последнего поста для {domain} из {settings.app.state_file}...")
    state = await _load_state()
    post_id = state.root.get(domain, 0)
    print(f"✅ ID последнего поста для {domain}: {post_id}")
    return post_id


async def set_last_post_id(domain: str, post_id: int) -> None:
    """Writes the last processed post ID for a specific domain to the state file."""
    print(f"💾 Записываю ID последнего поста для {domain} в {settings.app.state_file}...")
    state = await _load_state()
    state.root[domain] = post_id
    await _save_state(state)
    print(f"✅ ID последнего поста для {domain} обновлен: {post_id}")
