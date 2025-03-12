from dotenv import load_dotenv
import os
import logging
import time

from selenium import webdriver
from selenium.common import TimeoutException, WebDriverException
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

# Prometheus metric
PAGE_LOAD_TIME = Gauge('page_load_time_seconds', 'Page Load Time for monitored urls', ['url'])

def go(urls, timeout=30, frequency=60):

    freq_rate = 1.0

    def pause_time_evaluator():
        pause_time = round((frequency / len(urls) * freq_rate), 2)
        logger.info(f"Pause between requests was set to {pause_time} sec for {freq_rate} rate")
        return pause_time

    sleep_between = pause_time_evaluator()

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
                logger.warning(f"Timed out! {url}: {load_time:.2f} sec")

            except WebDriverException as err:
                logger.warning(f"WebDriverException with {url}: {err.msg.splitlines()[0]}")

            # pause before sending next request
            stage_time = sleep_between - (time.time() - start_time)
            time.sleep(stage_time if stage_time > 0 else 0)

        driver.quit()

        # pause before next cycle
        slp_time = frequency - (time.time() - commence_time)
        if slp_time >= 0:
            logger.info(f"Pause:' {slp_time:.2f} sec")
        else:
            logger.warning(f"Not enough time to perform {len(urls)} requests in {frequency} sec")

        time.sleep(slp_time if slp_time > 0 else 0)
        logger.info(f"Free time at the end of the task: {slp_time}")

if __name__ == "__main__":
    # Prometheus HTTP-server
    start_http_server(8015)

    go(url_list)

# TODO:Error after deployment
# Traceback (most recent call last):
#   File "/app/mon_page_load.py", line 120, in <module>
#     go(url_list)
#   File "/app/mon_page_load.py", line 75, in go
#     driver = webdriver.Chrome(service=service, options=chrome_options)
#   File "/usr/local/lib/python3.10/site-packages/selenium/webdriver/chrome/webdriver.py", line 45, in __init__
#     super().__init__(
#   File "/usr/local/lib/python3.10/site-packages/selenium/webdriver/chromium/webdriver.py", line 55, in __init__
#     self.service.start()
#   File "/usr/local/lib/python3.10/site-packages/selenium/webdriver/common/service.py", line 104, in start
#     self._start_process(self._path)
#   File "/usr/local/lib/python3.10/site-packages/selenium/webdriver/common/service.py", line 238, in _start_process
#     raise WebDriverException(
# selenium.common.exceptions.WebDriverException: Message: 'chromedriver' executable may have wrong permissions.