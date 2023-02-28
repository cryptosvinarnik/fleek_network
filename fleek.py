import asyncio

import httpx
from anti_useragent import UserAgent
from bs4 import BeautifulSoup
from loguru import logger

from config import HEADERS


def get_modified_headers() -> dict:
    headers = HEADERS.copy()
    headers["User-Agent"] = UserAgent().random

    return headers


class Fleek():
    def __init__(self):
        self._client = httpx.AsyncClient(
            headers=get_modified_headers()
        )

    def __del__(self):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._client.aclose())
            else:
                loop.run_until_complete(self._client.aclose())
        except Exception:
            pass

    async def request(self, method: str, url: str, json: dict | None = None, data: dict | str | None = None) -> httpx.Response:
        response = await self._client.request(method=method, url=url, json=json, data=data, follow_redirects=True)

        logger.info(
            f"{method} {response.url} Response: '{response.status_code}"
        )

        return response
    
    async def get_fleek_html(self) -> str:
        response = await self.request(method="GET", url="https://fleek.network/")

        return response.text
    
    async def submit_form(self, data: dict):
        response = await self.request(method="POST", url="https://fleek.activehosted.com/proc.php", data=data)

        return response
    
    @staticmethod
    def parse_form(html: str) -> tuple:
        soup = BeautifulSoup(html, "html.parser")
        form = soup.find("form", id="subscribe-for-updates")

        action = form["action"]
        data = {}
        for input_tag in form.find_all("input"):
            name = input_tag.get("name")
            value = input_tag.get("value")
            if name and value:
                data[name] = value

        return (action, data)


async def subscribe_fleek(queue: asyncio.Queue):
    while not queue.empty():
        fleek = Fleek()

        html = await fleek.get_fleek_html()
        action, data = fleek.parse_form(html)

        data["email"] = (email := await queue.get())

        logger.info(f"Fetched {action} with data {data}")

        response = await fleek.submit_form(data)

        if "forms thank-you" in (text := response.text):
            logger.success(f"Subscribed {email} to Fleek")
            continue

        logger.error(f"Failed to subscribe {email} to Fleek: {text[:50]}")
