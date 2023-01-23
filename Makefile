# define the name of the virtual environment directory
VENV := .venv

# default target, when make executed without arguments
all: venv

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	./$(VENV)/bin/pip install -r requirements.txt

# venv is a shortcut target
venv: $(VENV)/bin/activate

vars:
	(echo "DJANGO_SECRET_KEY" && openssl rand -base64 45) | tr "\n" "=" > .env

test:
	./$(VENV)/bin/pytest -k Crawler

run: venv
	./$(VENV)/bin/python3 manage.py runserver
	./$(VENV)/bin/celery -A sample_crawler worker -c 100 -l INFO

clean:
	rm -rf $(VENV)
	find . | grep -E "(/__pycache__$|/\.pytest_cache$|\.pyc$|\.pyo)" | xargs rm -rf

.PHONY: all venv run clean