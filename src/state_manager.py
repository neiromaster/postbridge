import os
from typing import Dict

import yaml

from .config import settings


def _load_state() -> Dict[str, int]:
    """Loads the state from the YAML file."""
    if not os.path.exists(settings.app.state_file):
        return {}
    try:
        with open(settings.app.state_file, "r") as f:
            state = yaml.safe_load(f)
            return state if state else {}
    except (yaml.YAMLError, FileNotFoundError):
        return {}


def _save_state(state: Dict[str, int]) -> None:
    """Saves the state to the YAML file."""
    with open(settings.app.state_file, "w") as f:
        yaml.dump(state, f, indent=4)


def get_last_post_id(domain: str) -> int:
    """Reads the last processed post ID for a specific domain from the state file."""
    print(f"\n💾 Читаю ID последнего поста для {domain} из {settings.app.state_file}...")
    state = _load_state()
    post_id = state.get(domain, 0)
    print(f"✅ ID последнего поста для {domain}: {post_id}")
    return post_id


def set_last_post_id(domain: str, post_id: int) -> None:
    """Writes the last processed post ID for a specific domain to the state file."""
    print(f"💾 Записываю ID последнего поста для {domain} в {settings.app.state_file}...")
    state = _load_state()
    state[domain] = post_id
    _save_state(state)
    print(f"✅ ID последнего поста для {domain} обновлен: {post_id}")
