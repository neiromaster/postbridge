import asyncio
import signal
import sys

from src.app import run_app
from src.managers.telegram_client_manager import TelegramClientManager
from src.managers.vk_client_manager import VKClientManager
from src.managers.ytdlp_manager import YtDlpManager


async def main() -> None:
    shutdown_event = asyncio.Event()

    # On Linux/macOS, you can use signals
    if sys.platform != "win32":
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, shutdown_event.set)
        loop.add_signal_handler(signal.SIGTERM, shutdown_event.set)

    # Initialization of managers
    vk_manager = VKClientManager(shutdown_event)
    tg_manager = TelegramClientManager(shutdown_event)
    ytdlp_manager = YtDlpManager(shutdown_event)

    await vk_manager.start()
    await tg_manager.start()
    await ytdlp_manager.start()

    try:
        await run_app(shutdown_event, vk_manager, tg_manager, ytdlp_manager)
    except KeyboardInterrupt:
        print("\n🧹 Завершение по Ctrl+C.")
        shutdown_event.set()
    finally:
        print("🛑 Останавливаю сервисы...")
        await ytdlp_manager.stop()
        await tg_manager.stop()
        await vk_manager.stop()
        print("✅ Завершено.")


if __name__ == "__main__":
    asyncio.run(main())
