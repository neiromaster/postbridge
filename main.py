import asyncio
from src.app import run_app

if __name__ == "__main__":
    try:
        asyncio.run(run_app())
    except KeyboardInterrupt:
        print("\nBot stopped manually.")
