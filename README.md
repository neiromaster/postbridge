# Postbridge

This script monitors a VK community wall for new posts, downloads any attached videos, and publishes them to a Telegram channel using your personal account (via Telethon) to support files up to 2 GB.

## Setup

1. **Install dependencies.**
    You must have [uv](https://github.com/astral-sh/uv) installed.

    ```bash
    uv pip install -r requirements.txt
    ```

2. **Configure environment variables.**
    Copy `.env.example` to `.env` and fill in your details.

    - `VK_SERVICE_TOKEN`: The service access key for your VK application.
    - `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`: Get these from [my.telegram.org](https://my.telegram.org) under "API development tools".

3. **Configure the configuration file.**
    Edit the `config.yaml` file to configure the script's behavior.

4. **Authorize in VK in your browser.**
    `yt-dlp` requires cookies to download videos. Log in to your `vk.com` account in the browser you specified in `config.yaml` (in the `downloader` section, `browser` parameter).

## Configuration (`config.yaml`)

- **`app`**:
  - `wait_time_seconds`: The pause in seconds between checking for new posts.
- **`vk`**:
  - `domain`: The short name or ID of the VK community (e.g., `durov`).
  - `post_count`: The number of posts to request with each check.
  - `post_source`: The source of the posts. Can be `wall` (regular posts) or `donut` (for VK Donut paid subscribers).
- **`telegram`**:
  - `channel_ids`: A list of your Telegram channel IDs (e.g., `@my_channel` or `-100123456789`).
- **`downloader`**:
  - `browser`: The browser from which cookies will be imported for `yt-dlp` (e.g., `chrome`, `firefox`, `edge`).
  - `output_path`: The directory to save downloaded videos.
  - `yt_dlp_opts`: Options for `yt-dlp`.
    - `concurrent_fragment_downloads`: The number of fragments to download simultaneously.
    - `skip_unavailable_fragments`: Whether to skip unavailable fragments.
    - `fragment_retries`: The number of download attempts for each fragment.
    - `retries`: The total number of download attempts.
    - `external_downloader`: The external downloader to use (`aria2c`, `native`).
    - `external_downloader_args`: Arguments for the external downloader.

## Running the script

    ```bash
    uv run python main.py
    ```

### Important: First run

On the first run, `kurigram` will ask you to enter your phone number, a code from Telegram, and possibly your two-factor authentication password directly in the console. After successful authorization, a `user_session.session` file will be created, and subsequent logins will be automatic.
