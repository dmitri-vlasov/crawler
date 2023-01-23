import asyncio
import pickle

import redis
from django.conf import settings

from sample_crawler.celery import app, logger
from sample_crawler.crawler import retrieve_links_from_urls

redis_client = redis.Redis(charset="utf-8", decode_responses=True)


@app.task
def crawl_to_redis(urls: list[str], depth: int = 1) -> None:
    """
    Celery task to crawl specified URL and cache results to Redis.
    :param urls: URLs to crawl
    :param depth: controls crawl depth
    :return: None
    """
    logger.info(f'Crawling {len(urls)} urls with depth {depth}')

    # don't crawl what is already cached
    links_pickled = redis_client.keys('http*')
    urls_to_crawl = [url for url in urls if url not in links_pickled]

    if urls_to_crawl:
        links_data = asyncio.run(retrieve_links_from_urls(urls_to_crawl))

        for url, links in links_data.items():
            redis_client.set(
                url, pickle.dumps(links), ex=settings.CRAWL_RESULTS_EXPIRATION_SECONDS
            )
            # spawn Celery tasks to crawl links we found
            # if we haven't reached a desired depth yet
            if depth <= settings.CRAWL_DEPTH:
                links_limit = settings.LINKS_LIMIT or len(urls)
                if links[:links_limit]:
                    crawl_to_redis.delay(links[:links_limit], depth=depth + 1)
