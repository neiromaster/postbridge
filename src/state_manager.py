import os

LAST_POST_ID_FILE = "last_post_id.txt"

def get_last_post_id():
    """Reads the last processed post ID from the state file."""
    if not os.path.exists(LAST_POST_ID_FILE):
        return 0
    with open(LAST_POST_ID_FILE, "r") as f:
        content = f.read().strip()
        return int(content) if content.isdigit() else 0

def set_last_post_id(post_id):
    """Writes the last processed post ID to the state file."""
    with open(LAST_POST_ID_FILE, "w") as f:
        f.write(str(post_id))
