"""Quick script to test chrome_client.check_frontend locally.

Run with your Python env where Playwright is installed and browsers are installed:
python mcp/test_chrome_client.py
"""
import asyncio
from .chrome_client import check_frontend


async def main():
    res = await check_frontend("http://localhost:3000", wait_selector="body", timeout=6, screenshot=False)
    print(res)


if __name__ == "__main__":
    asyncio.run(main())
