FROM python:3-slim
LABEL maintainer="nick@buonincontri.org"

ENV PYTHONUNBUFFERED 1
ENV PIPENV_VENV_IN_PROJECT 1
EXPOSE 8000

RUN pip3 install pipenv
COPY . /app/
WORKDIR /app/

RUN set -ex && \
    pipenv sync && \
    useradd wagtail && \
    chown -R wagtail /app

USER wagtail

CMD pipenv run ./manage.py collectstatic && \
    pipenv run ./manage.py migrate && \
    pipenv run gunicorn --bind 0.0.0.0:8000 --workers 3 --forwarded-allow-ips="*" chelseasymphony.wsgi:application
