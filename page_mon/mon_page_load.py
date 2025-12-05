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
    while True:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True,
                                                  args=[
                                                      "--no-sandbox",
                                                      "--disable-dev-shm-usage",
                                                      "--disable-gpu",
                                                      "--disable-software-rasterizer",
                                                      "--disable-features=VizDisplayCompositor",
                                                      "--disable-ipc-flooding-protection",
                                                      "--disable-background-timer-throttling",
                                                      "--single-process",
                                                      "--no-zygote",
                                                  ]
                                              )
            cycle_start_time = time.time()
            urls_queue = list(urls)

            while urls_queue:
                url = urls_queue.pop(0)

                context = None

                try:
                    context = await browser.new_context()
                    page = await context.new_page()

                    start_time = time.time()
                    await page.goto(url, timeout=timeout * 1000, wait_until="load")
                    load_time = time.time() - start_time

                    logger.info(f"Load Time {url}: {load_time:.2f} sec")
                    PAGE_LOAD_TIME.labels(url=url).set(load_time)

                except Exception as e:
                    logger.warning(f"Error loading {url}: {str(e)}")

                finally:
                    try:
                        await context.close()
                        logger.debug(f"Context closed for {url}")
                    except Exception as e:
                        logger.error(f"Failed to close context for {url}: {e}")

                # remaining time to complete cycle
                elapsed_cycle = time.time() - cycle_start_time
                remaining_time = frequency - elapsed_cycle

                remaining_count = len(urls_queue)

                if remaining_count > 0 and remaining_time > 0:
                    next_pause = remaining_time / remaining_count
                    logger.debug(f"Next pause: {next_pause:.2f} sec")
                    await asyncio.sleep(next_pause)
                else:
                    logger.debug(f"No pause, finishing cycle soon")

            try:
                await p.stop()
            except Exception as e:
                logger.warning(f"Playwright driver stop failed: {e}")

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
