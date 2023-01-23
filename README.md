# Sample crawler

## About

Django web app that has one text input field and a "go" button. The field accepts a URL of a web page (for example https://en.wikipedia.org/wiki/Django_(web_framework)).
 
After you click the "go" button, the app crawls all the URLs in the given webpage and displays to the customer a complete list of all the URLs the crawler found, including nested links.

It shows empty list of list in case of error accessing a web page (both ways, 4xx and 5xx).

## Installation and usage

1. Install required packages:

```shell
pip install -r requirements.txt
```

2. [Install Redis server](https://redis.io/docs/getting-started/installation/), run it and adjust the connection string in `settings.py`.
3. Run webserver and worker for background tasks: 
```shell
python3 manage.py runserver
celery -A sample_crawler worker -c 100 -l DEBUG
```