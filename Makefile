ROOT_DIR := .
DOCS_DIR := $(ROOT_DIR)/docs
DOCS_BUILD_DIR := $(DOCS_DIR)/_build

PROJECT_NAME := yo
PROJECT_DOCKER_TAG := steemit/$(PROJECT_NAME)

default: install-global

.PHONY: docker-image build-without-docker test-without-lint test-pylint test-without-build install-pipenv install-global clean clean-build

docker-image: clean
	docker build -t $(PROJECT_DOCKER_TAG) .

Pipfile.lock: Pipfile
	python3.6 -m pipenv --python /usr/local/bin/python3.6 lock

requirements.txt: Pipfile.lock
	python3.6 -m pipenv --python /usr/local/bin/python3.6 lock -r | grep -v Using | >requirements.txt

.env: ${YO_CONFIG} scripts/make_docker_env.py
	python3.6 scripts/make_docker_env.py ${YO_CONFIG} >.env

build-without-docker: requirements.txt Pipfile.lock
	mkdir -p build/wheel
	python3.6 -m pipenv install --python /usr/local/bin/python3.6 --dev
	python3.6 -m pipenv run python3.6 setup.py build

dockerised-test: docker-image
	docker run -ti $(PROJECT_DOCKER_TAG) make -C /app test-without-lint

test: build-without-docker test-without-build

test-without-build: test-without-lint test-pylint

test-without-lint:
	pipenv run python3.6 -m pytest -vv --cov=yo --cov-report term --cov-report html:cov_html tests/

test-pylint:
	pipenv run pytest -v --pylint

clean: clean-build clean-pyc
	rm -rf requirements.txt

clean-build:
	rm -fr build/ dist/ *.egg-info .eggs/ .tox/ __pycache__/ .cache/ .coverage htmlcov src

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

install-pipenv: clean
	python3.6 -m pipenv run pip3.6 install -e .

install-global: clean
	pip3.6 install -e .

pypi:
	python3.6 setup.py bdist_wheel --universal
	python3.6 setup.py sdist bdist_wheel upload

.PHONY: install-python-steem-macos
install-python-steem-macos: ## install steem-python lib on macos using homebrew's openssl
	env LDFLAGS="-L$(brew --prefix openssl)/lib" CFLAGS="-I$(brew --prefix openssl)/include" pipenv install steem
