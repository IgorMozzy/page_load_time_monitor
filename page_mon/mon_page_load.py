from dotenv import load_dotenv
import os
import logging
import time

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from prometheus_client import start_http_server, Gauge

# logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# log to console
ENABLE_CONSOLE_LOG = True

#TODO: optional handler to write a file
if ENABLE_CONSOLE_LOG:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

load_dotenv()

env_urls = os.getenv("URLS")

if env_urls:
    url_list = env_urls.splitlines()
else:
    url_list = []

logger.info(f"Got URLs to check: {url_list}")

# trying to lower chromedriver CPU usage
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-background-timer-throttling")
chrome_options.add_argument("--disable-backgrounding-occluded-windows")
chrome_options.add_argument("--disable-client-side-phishing-detection")
chrome_options.add_argument("--disable-renderer-backgrounding")
chrome_options.add_argument("--disable-crash-reporter")
chrome_options.add_argument("--disable-oopr-debug-crash-dump")
chrome_options.add_argument("--no-crash-upload")
chrome_options.add_argument("--silent")
chrome_options.add_argument("--remote-debugging-pipe")

service = Service('/app/chromedriver')

# Метрика Prometheus
PAGE_LOAD_TIME = Gauge('page_load_time_seconds', 'Page Load Time for monitored sites', ['url'])

def go(urls, timeout=30):
    while True:
        commence_time = time.time()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(timeout)
        # browser warm up
        try:
            driver.get('localhost')
        except:
            pass
        # real tasks
        for url in urls:
            start_time = time.time()
            try:
                driver.get(url)
                load_time = time.time() - start_time
                logger.info(f"Load Time {url}: {load_time:.2f} sec")

                PAGE_LOAD_TIME.labels(url=url).set(time.time() - start_time)

            except TimeoutException:
                load_time = time.time() - start_time
                logger.warning(f"Timed out! {url}: {load_time:.2f} sec")

                PAGE_LOAD_TIME.labels(url=url).set(load_time)
            stage_time = 10 - (time.time() - start_time)
            time.sleep(stage_time if stage_time > 0 else 0)
        driver.quit()
        slp_time = 70 - (time.time() - commence_time)
        logger.info(f"Pause:' {slp_time:.2f} sec")
        time.sleep(slp_time if slp_time > 0 else 0)

if __name__ == "__main__":
    # Prometheus HTTP-server
    start_http_server(8015)

    go(url_list)
