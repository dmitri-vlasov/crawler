import asyncio
import logging
from urllib.parse import urlparse

import aiohttp
import requests
from django.conf import settings
from lxml.etree import Error as LxmlError
from lxml.html import fromstring

logger = logging.getLogger('django')


async def retrieve_links_from_url(
    url: str, session: aiohttp.ClientSession
) -> tuple[str, list]:
    try:
        async with session.get(url, headers=settings.CRAWLER_HEADERS) as response:
            return url, extract_links_data(await response.text(), url)

    except Exception as ex:
        logger.error(f'An error occurred while accessing a page {url}: {ex}')
        return url, []


async def retrieve_links_from_urls(urls: list[str]) -> dict[str, str]:
    """
    Returns a dict with urls as keys and
    links parsed from them as values.
    :param urls: url to request
    :return:
    """
    timeout = aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        print(urls)
        links_data = await asyncio.gather(
            *[retrieve_links_from_url(url, session) for url in urls],
            return_exceptions=True,
        )
        return {url: links for url, links in links_data}


def extract_links_data(html_page: str, url: str) -> list | list[str]:
    """
    Extracts links from HTML. Related links converted to absolute.
    :param html_page:
    :param url:
    :return:
    """
    url_components = urlparse(url)
    root_url = f'{url_components.scheme}://{url_components.netloc}'

    try:
        selector = fromstring(html_page)
        # grab only those having href
        links_elements = selector.xpath('//a[(@href)]')
        links_data = []

        for a_element in links_elements:
            # fix relative urls
            link_url = requests.compat.urljoin(root_url, a_element.xpath('@href')[0])
            links_data.append(link_url)

    except LxmlError:
        links_data = []

    return links_data
