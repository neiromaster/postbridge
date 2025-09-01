import os
import yaml
from dotenv import load_dotenv

load_dotenv()


# --- Load Configuration from YAML ---
def load_config():
    """Loads configuration from config.yaml. Returns empty dict if not found."""
    print("Attempting to load configuration from config.yaml...")
    if not os.path.exists("config.yaml"):
        print("Warning: config.yaml not found. Using default settings where possible.")
        return {}
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
        print("Configuration loaded successfully.")
        return config if config else {}
    except Exception as e:
        print(f"Warning: Could not read config.yaml. Error: {e}. Using default settings.")
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

# VK settings
VK_CONFIG = config.get("vk", {})
VK_DOMAIN = VK_CONFIG.get("domain")
VK_POST_COUNT = VK_CONFIG.get("post_count", 10)

# Telegram settings
TELEGRAM_CONFIG = config.get("telegram", {})
TELEGRAM_CHANNEL_ID = TELEGRAM_CONFIG.get("channel_id")

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
    if not VK_DOMAIN:
        raise ValueError("The 'domain' key under the 'vk' section is not set in config.yaml")
    if not TELEGRAM_CHANNEL_ID:
        raise ValueError("The 'channel_id' key under the 'telegram' section is not set in config.yaml")


validate_configuration()
