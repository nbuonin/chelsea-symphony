FROM python:3-slim
LABEL maintainer="nick@buonincontri.org"

ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev

RUN pip3 install pipenv

COPY . /app/
WORKDIR /app/

RUN set -ex && \
    pipenv sync 
#    useradd wagtail && \
#    chown -R wagtail /app

# USER wagtail

EXPOSE 8000
CMD pipenv run gunicorn chelseasymphony.wsgi:application --bind 0.0.0.0:8000 --workers 3
