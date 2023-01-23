from urllib.parse import urlparse

import requests
from django.conf import settings
from lxml.html import fromstring
from lxml.etree import Error as LxmlError


def get_html_for_url(url: str) -> str:
    """
    Requests the given url and returns its HTML.
    :param url: url to request
    :return: HTML as a string
    """
    with requests.Session() as session:

        response = session.get(
            url, headers=settings.CRAWLER_HEADERS, timeout=settings.REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response.text


def extract_links_data(html_page: str, url: str) -> list:
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
