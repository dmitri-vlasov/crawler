from sample_crawler.crawler import extract_links_data, get_html_for_url


class TestCrawler:
    """
    Test crawler's features.
    """

    test_url = 'https://httpbin.org'

    def test_get_html_for_url(self):
        html_page = get_html_for_url(TestCrawler.test_url)
        assert html_page.lower().startswith('<!doctype html>')

    def test_extract_links_data(self):
        html_page = get_html_for_url(TestCrawler.test_url)
        links = extract_links_data(html_page, TestCrawler.test_url)
        assert len(links) > 0 and not all(link.startswith('http') for link in links)
