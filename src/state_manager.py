import os

import yaml

STATE_FILE = "state.yaml"


def _load_state():
    """Loads the state from the YAML file."""
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            state = yaml.safe_load(f)
            return state if state else {}
    except (yaml.YAMLError, FileNotFoundError):
        return {}


def _save_state(state):
    """Saves the state to the YAML file."""
    with open(STATE_FILE, "w") as f:
        yaml.dump(state, f, indent=4)


def get_last_post_id(domain):
    """Reads the last processed post ID for a specific domain from the state file."""
    print(f"💾 Читаю ID последнего поста для {domain} из {STATE_FILE}...")
    state = _load_state()
    post_id = state.get(domain, 0)
    print(f"✅ ID последнего поста для {domain}: {post_id}")
    return post_id


def set_last_post_id(domain, post_id):
    """Writes the last processed post ID for a specific domain to the state file."""
    print(f"💾 Записываю ID последнего поста для {domain} в {STATE_FILE}...")
    state = _load_state()
    state[domain] = post_id
    _save_state(state)
    print(f"✅ ID последнего поста для {domain} обновлен: {post_id}")
