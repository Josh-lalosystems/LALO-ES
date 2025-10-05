"""Quick script to test chrome_client.check_frontend locally.

Run with your Python env where Playwright is installed and browsers are installed:
python mcp/test_chrome_client.py
"""
import asyncio
import logging
from .chrome_client import check_frontend

logger = logging.getLogger("lalo.mcp.test_chrome_client")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


async def main():
    res = await check_frontend("http://localhost:3000", wait_selector="body", timeout=6, screenshot=False)
    logger.info("chrome_client.check_frontend result: %s", res)


if __name__ == "__main__":
    asyncio.run(main())
