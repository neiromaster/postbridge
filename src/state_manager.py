import os

LAST_POST_ID_FILE = "last_post_id.txt"


def get_last_post_id():
    """Reads the last processed post ID from the state file."""
    print(f"Reading last post ID from {LAST_POST_ID_FILE}...")
    if not os.path.exists(LAST_POST_ID_FILE):
        print("File not found. Returning 0.")
        return 0
    with open(LAST_POST_ID_FILE, "r") as f:
        content = f.read().strip()
        post_id = int(content) if content.isdigit() else 0
        print(f"Found last post ID: {post_id}")
        return post_id


def set_last_post_id(post_id):
    """Writes the last processed post ID to the state file."""
    print(f"Writing last post ID {post_id} to {LAST_POST_ID_FILE}...")
    with open(LAST_POST_ID_FILE, "w") as f:
        f.write(str(post_id))
    print("Successfully wrote to state file.")
