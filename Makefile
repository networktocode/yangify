ifeq (${PYTHON}, )
override PYTHON=3.6
endif

NAME=yangify
DOCKER=docker run -it -v $(PWD):/yangify yangify-${PYTHON}:latest
DEV_JUPYTER=docker run -p 8888:8888 -v $(PWD):/yangify ${NAME}-${PYTHON}:latest
DEV_ME=docker run -it -v $(PWD):/yangify ${NAME}-${PYTHON}:latest /bin/bash


.PHONY: clean
clean:
	find . -name "__pycache__" -type d -exec rm -rf {} \; | exit 0
	rm -rf docs/tutorials/.ipynb_checkpoints | exit 0
	rm -rf docs/tutorials/parsing-quickstart/.ipynb_checkpoints | exit 0

.PHONY: build_test_container
build_test_container: clean
	docker build --tag ${NAME}-${PYTHON}:latest --build-arg PYTHON=${PYTHON} -f Dockerfile .

.PHONY: build_test_containers
build_test_containers:
	make build_test_container PYTHON=3.6
	make build_test_container PYTHON=3.7

.PHONY: clean_container
clean_container:
	docker stop $(NAME); \
	docker rm $(NAME);

.PHONY: _clean_image
_clean_image:
	docker rmi ${NAME}-${PYTHON}:latest --force;

.PHONY: clean_images
clean_images:
	make _clean_image PYTHON=3.6
	make _clean_image PYTHON=3.7

.PHONY: rebuild_docker_images
rebuild_docker_images:
	make clean_images | exit 0
	make build_test_containers

.PHONY: enter_container
enter_container:
	${DOCKER} \
		bash

.PHONY: pytest
pytest:
	${DOCKER} \
		pytest --cov=yangify --cov-report=term-missing -vvvvvvs ${ARGS}

.PHONY: black
black:
	${DOCKER} \
		black --check .

.PHONY: sphinx_test
sphinx_test:
	${DOCKER} \
		sphinx-build -W -n -E -q -N -b dummy -d docs/_build/doctrees docs /tmp/

.PHONY: pylama
pylama:
	${DOCKER} \
		pylama .

.PHONY: mypy
mypy:
	${DOCKER} \
		mypy .

.PHONY: _nbval_docker
_nbval_docker:
	/root/.poetry/bin/poetry install
	pytest --nbval \
		docs/tutorials

.PHONY: nbval
nbval:
	${DOCKER} \
		make _nbval_docker

.PHONY: _docs
_docs:
	cd docs && make html

.PHONY: docs
docs:
	${DOCKER} \
			make _docs

.PHONY: install
install:
	/root/.poetry/bin/poetry install

.PHONY: _jupyter
_jupyter:
	/root/.poetry/bin/poetry install
	jupyter notebook --allow-root --ip=0.0.0.0 --NotebookApp.token=''

.PHONY: jupyter
jupyter:
	${DEV_JUPYTER} \
		make _jupyter

.PHONY: _jupyter_save
_jupyter_save:
	/root/.poetry/bin/poetry install
	jupyter nbconvert --to notebook --inplace --execute docs/tutorials/*.ipynb

.PHONY: jupyter_save
jupyter_save:
	${DOCKER} \
		make _jupyter_save


.PHONY: dev_jupyter
dev_jupyter:
	${DEV_JUPYTER} \
		make _jupyter

.PHONY: enter_dev_container
enter_dev_container:
	${DEV_ME}

PHONY: tests
tests: build_test_containers black sphinx_test pylama mypy nbval
	make pytest PYTHON=3.6
	make pytest PYTHON=3.7
