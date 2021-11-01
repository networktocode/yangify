ARG PYTHON

FROM python:${PYTHON}-stretch

RUN apt-get update && apt-get install -y pandoc

RUN pip install --no-cache-dir poetry==1.0.0 && poetry config virtualenvs.create false && pip install --no-cache-dir -U pip

ADD poetry.lock /tmp
ADD pyproject.toml /tmp
RUN cd /tmp && poetry install

ADD docs/requirements.txt /tmp/requirements-docs.txt
RUN pip install --no-cache-dir -r /tmp/requirements-docs.txt

ADD . /yangify

WORKDIR "/yangify"
