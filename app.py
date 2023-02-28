import asyncio

from config import WORKERS
from fleek import subscribe_fleek


async def main():
    with open(input("File with emails: ")) as f:
        emails = f.read().splitlines()

    queue = asyncio.Queue()

    for email in emails:
        queue.put_nowait(email)

    tasks = [
        asyncio.create_task(subscribe_fleek(queue))
        for _ in range(WORKERS)
    ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception:
        pass