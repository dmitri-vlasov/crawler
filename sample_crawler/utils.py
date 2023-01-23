from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    parsed_url = urlparse(url)
    return parsed_url.scheme is not None and parsed_url.netloc is not None
