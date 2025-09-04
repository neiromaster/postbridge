import asyncio

from src.app import run_app


async def main():
    shutdown_event = asyncio.Event()

    try:
        await run_app(shutdown_event)
    except asyncio.CancelledError:
        print("Application tasks cancelled.")
    finally:
        print("Main application loop finished.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped manually (KeyboardInterrupt).")
