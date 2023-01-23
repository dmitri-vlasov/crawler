import logging
import pickle
from urllib.parse import urlparse

import redis
import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView

from sample_crawler.celery import crawl_to_redis
from sample_crawler.crawler import extract_links_data, get_html_for_url

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
        links_cached = redis_client.get(url)

        url_components = urlparse(url)
        if not url_components.scheme or not url_components.netloc:
            context['error'] = 'Oh, boy! URL is not valid'
            return self.render_to_response(context)

        if links_cached:
            context['links'] = pickle.loads(links_cached)

        else:
            try:
                html_page = get_html_for_url(url)
                context['links'] = extract_links_data(html_page, url)
                redis_client.set(
                    url,
                    pickle.dumps(context['links']),
                    ex=settings.CRAWL_RESULTS_EXPIRATION_SECONDS,
                )

                # crawl nested links on background
                slice_to = settings.LINKS_LIMIT or len(context['links'])
                for link in context['links'][:slice_to]:
                    crawl_to_redis.delay(link, 1)

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
    links_pkl = redis_client.get(url)

    if links_pkl:
        data = pickle.loads(links_pkl)
    else:
        try:
            html_page = get_html_for_url(url)
            data = extract_links_data(html_page, url)

        except requests.RequestException as ex:
            error_msg = f'An error occurred while accessing a page {url}: {ex}'
            logger.error(error_msg)
            data = []

    return JsonResponse(data, safe=False)
