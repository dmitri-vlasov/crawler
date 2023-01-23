import logging
import os
import pickle

import redis
import requests
from celery import Celery
from django.conf import settings

from sample_crawler.crawler import extract_links_data, get_html_for_url

logger = logging.getLogger('django')
redis_client = redis.Redis()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sample_crawler.settings')

app = Celery('sample_crawler', broker=settings.CELERY_BROKER)

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task
def crawl_to_redis(url: str, depth: int) -> None:
    """
    Celery task to crawl specified URL and cache results to Redis.
    :param url: URL to crawl
    :param depth: controls crawl depth
    :return: None
    """
    logger.info(f'Crawling {url} with depth {depth}')

    links_pickled = redis_client.get(url)
    if not links_pickled:
        try:
            html_page = get_html_for_url(url)
            links = extract_links_data(html_page, url)

            if depth <= settings.CRAWL_DEPTH:
                slice_to = settings.LINKS_LIMIT or len(links)
                for link in links[:slice_to]:
                    crawl_to_redis.delay(link, depth + 1)

        except requests.RequestException as ex:
            logger.error(f'An error occurred while accessing a page {url}: {ex}')
            links = []  # cache anyway

        redis_client.set(
            url, pickle.dumps(links), ex=settings.CRAWL_RESULTS_EXPIRATION_SECONDS
        )
