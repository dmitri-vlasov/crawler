import asyncio
import logging
import pickle

import redis
import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView

from sample_crawler.crawler import retrieve_links_from_urls
from sample_crawler.tasks import crawl_to_redis
from sample_crawler.utils import is_valid_url

logger = logging.getLogger('django')
redis_client = redis.Redis()


class CrawlerView(TemplateView):
    template_name = 'index.html'

    def post(self, request) -> HttpResponse:
        """
        Crawls the given url for the links
        :param request: requests obj
        :return: HttpResponse
        """
        url = request.POST.get('url')
        context = {'submitted_url': url}

        if not is_valid_url(url):
            context['error'] = 'Oh, boy! URL is not valid'

        links_pickled = redis_client.get(url)

        if links_pickled:
            context['links'] = pickle.loads(links_pickled)
            return self.render_to_response(context)

        try:
            links_data = asyncio.run(retrieve_links_from_urls([url]))
            # we always have one url here
            context['links'] = links_data[url]
            redis_client.set(
                url,
                pickle.dumps(context['links']),
                ex=settings.CRAWL_RESULTS_EXPIRATION_SECONDS,
            )

            # crawl nested links on background
            links_limit = settings.LINKS_LIMIT or len(context['links'])
            crawl_to_redis.delay(context['links'][:links_limit], 1)

        except requests.RequestException as ex:
            error_msg = f'An error occurred while accessing a page {url}: {ex}'
            logger.error(error_msg)
            context['error'] = error_msg

        return self.render_to_response(context)


def get_nested_links(request) -> JsonResponse:
    """
    Either returns the nested links from Redis cache
    or crawls from web if cache is empty.
    :param request: requests obj
    :return: JsonResponse
    """
    url = request.POST.get('url')

    if not is_valid_url(url):
        return JsonResponse([], safe=False)

    links_pickled = redis_client.get(url)

    if links_pickled:
        links = pickle.loads(links_pickled)
    else:
        try:
            links_data = asyncio.run(retrieve_links_from_urls([url]))
            # we always have one url here
            links = links_data[url]
            redis_client.set(
                url,
                pickle.dumps(links),
                ex=settings.CRAWL_RESULTS_EXPIRATION_SECONDS,
            )

            # crawl nested links on background
            links_limit = settings.LINKS_LIMIT or len(links)

            # set depth to one before limit to prefetch
            # and show to user only one level
            crawl_to_redis.delay(links[:links_limit], depth=settings.CRAWL_DEPTH - 1)

        except requests.RequestException as ex:
            error_msg = f'An error occurred while accessing a page {url}: {ex}'
            logger.error(error_msg)
            links = []

    return JsonResponse(links, safe=False)
