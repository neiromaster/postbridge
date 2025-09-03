import os

import yaml
from dotenv import load_dotenv

load_dotenv()


# --- Load Configuration from YAML ---
def load_config():
    """Loads configuration from config.yaml. Returns empty dict if not found."""
    print("⚙️  Загружаю конфигурацию из config.yaml...")
    if not os.path.exists("config.yaml"):
        print("⚠️  config.yaml не найден. Используются настройки по умолчанию.")
        return {}
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
        print("✅ Конфигурация успешно загружена.")
        return config if config else {}
    except Exception as e:
        print(f"⚠️  Не удалось прочитать config.yaml. Ошибка: {e}. Используются настройки по умолчанию.")
        return {}


# --- Configuration Objects ---
config = load_config()

# --- Secrets ---
VK_SERVICE_TOKEN = os.getenv("VK_SERVICE_TOKEN")
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")

# --- Expose Configuration Values ---
# App settings
APP_CONFIG = config.get("app", {})
WAIT_TIME_SECONDS = APP_CONFIG.get("wait_time_seconds", 60)

# Bindings settings
BINDINGS = config.get("bindings", [])

# Downloader settings
DOWNLOADER_CONFIG = config.get("downloader", {})
DOWNLOADER_BROWSER = DOWNLOADER_CONFIG.get("browser", "edge")
DOWNLOADER_OUTPUT_PATH = DOWNLOADER_CONFIG.get("output_path", "downloads")
YTDLP_OPTS = DOWNLOADER_CONFIG.get("yt_dlp_opts", {})


# --- Validate Configuration ---
def validate_configuration():
    """Validates that all necessary configuration variables are set."""
    # Validate secrets from .env
    if not VK_SERVICE_TOKEN:
        raise ValueError("VK_SERVICE_TOKEN is not set in your .env file")
    if not TELEGRAM_API_ID:
        raise ValueError("TELEGRAM_API_ID is not set in your .env file")
    if not TELEGRAM_API_HASH:
        raise ValueError("TELEGRAM_API_HASH is not set in your .env file")

    # Validate values from config.yaml
    if not BINDINGS:
        raise ValueError("The 'bindings' section is not set in config.yaml or is empty")

    for i, binding in enumerate(BINDINGS):
        if "vk" not in binding:
            raise ValueError(f"Binding {i} is missing the 'vk' section")
        if "telegram" not in binding:
            raise ValueError(f"Binding {i} is missing the 'telegram' section")

        vk_config = binding["vk"]
        if "domain" not in vk_config:
            raise ValueError(f"Binding {i} is missing the 'domain' key in the 'vk' section")
        if "post_source" not in vk_config:
            raise ValueError(f"Binding {i} is missing the 'post_source' key in the 'vk' section")
        if vk_config["post_source"] not in ["wall", "donut"]:
            raise ValueError(f"Binding {i} has an invalid 'post_source' value. It must be either 'wall' or 'donut'")

        telegram_config = binding["telegram"]
        if "channel_ids" not in telegram_config or not telegram_config["channel_ids"]:
            raise ValueError(f"Binding {i} is missing the 'channel_ids' key in the 'telegram' section or it is empty")


validate_configuration()
