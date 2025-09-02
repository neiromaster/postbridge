import os

LAST_POST_ID_FILE = "last_post_id.txt"


def get_last_post_id():
    """Reads the last processed post ID from the state file."""
    print(f"💾 Читаю ID последнего поста из {LAST_POST_ID_FILE}...")
    if not os.path.exists(LAST_POST_ID_FILE):
        print("Файл не найден. Начинаю с нуля.")
        return 0
    with open(LAST_POST_ID_FILE, "r") as f:
        content = f.read().strip()
        post_id = int(content) if content.isdigit() else 0
        print(f"✅ ID последнего поста: {post_id}")
        return post_id


def set_last_post_id(post_id):
    """Writes the last processed post ID to the state file."""
    with open(LAST_POST_ID_FILE, "w") as f:
        f.write(str(post_id))