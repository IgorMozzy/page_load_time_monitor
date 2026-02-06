import asyncio
import os
import time
import logging
from dotenv import load_dotenv
from prometheus_client import start_http_server, Gauge
from playwright.async_api import async_playwright


# load environment variables
load_dotenv()

# logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ENABLE_CONSOLE_LOG = os.getenv("ENABLE_CONSOLE_LOG", False)

if ENABLE_CONSOLE_LOG:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

env_urls = os.getenv("URLS")

if env_urls:
    url_list = env_urls.splitlines()
else:
    url_list = []

logger.info(f"Got URLs to check: {url_list}")

# Prometheus metric
# TODO: consider to add others new metrics from Playwright
PAGE_LOAD_TIME = Gauge('page_load_time_seconds',
                       'Page Load Time for monitored urls',
                       ['url'])

# Parameters
TIMEOUT = int(os.getenv("TIMEOUT", 30))      # seconds
FREQUENCY = int(os.getenv("FREQUENCY", 60))  # enqueue frequency

# TODO: consider implementation through semaphore
async def monitor(urls, timeout=30, frequency=60):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        while True:
            cycle_start_time = time.time()
            urls_queue = list(urls)

            while urls_queue:
                url = urls_queue.pop(0)

                context = await browser.new_context()
                page = await context.new_page()
                load_time = 0

                try:
                    start_time = time.time()
                    response = await page.goto(url, timeout=timeout * 1000, wait_until="load")

                    if response and 500 <= response.status < 600:
                        logger.warning(
                            f"Non-200 status code for {url}: {response.status if response else 'No Response'}")
                        load_time = 30
                    else:
                        load_time = time.time() - start_time

                    logger.info(f"Load Time {url}: {load_time:.2f} sec")
                    PAGE_LOAD_TIME.labels(url=url).set(load_time)

                except Exception as e:
                    logger.warning(f"Error loading {url}: {str(e)}")

                await context.close()

                # remaining time to complete cycle
                elapsed_cycle = time.time() - cycle_start_time
                remaining_time = frequency / 2 - elapsed_cycle

                remaining_count = len(urls_queue)

                if remaining_count > 0 and remaining_time > 0:
                    next_pause = remaining_time / remaining_count - load_time
                    logger.debug(f"Next pause: {next_pause:.2f} sec")
                    await asyncio.sleep(next_pause)
                else:
                    logger.debug(f"No pause, finishing cycle soon")

            # waiting for the next round
            total_elapsed = time.time() - cycle_start_time
            final_sleep = frequency - total_elapsed
            if final_sleep > 0:
                logger.info(f"Cycle complete, final sleep: {final_sleep:.2f} sec")
                await asyncio.sleep(final_sleep)
            else:
                logger.warning("Cycle overran the intended frequency!")

# before first start: RUN playwright install chromium
if __name__ == "__main__":
    # Start Prometheus HTTP-server
    start_http_server(8015)
    asyncio.run(monitor(url_list, timeout=TIMEOUT, frequency=FREQUENCY))