from sample_crawler.crawler import retrieve_links_from_urls


class TestCrawler:
    """
    Test crawler's features.
    """

    test_url = 'https://httpbin.org'

    def test_retrieve_links_from_urls(self):
        links_data = retrieve_links_from_urls([TestCrawler.test_url])
        links = links_data[TestCrawler.test_url]
        assert len(links) > 0 and not all(link.startswith('http') for link in links)
