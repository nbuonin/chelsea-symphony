runserver:
	pipenv run ./manage.py runserver

migrate:
	pipenv run ./manage.py migrate

makemigrations:
	pipenv run ./manage.py makemigrations

superuser:
	pipenv run ./manage.py createsuperuser

shell:
	pipenv run ./manage.py shell

test:
	pipenv run ./manage.py test

scss:
	npm run watch-scss

docker-image:
	docker build -t nbuonin/chelsea-symphony-wagtail:`git log -n 1 --pretty="%h"` .

docker-test:
	docker run --rm nbuonin/chelsea-symphony-wagtail:`git log -n 1 --pretty="%h"` pipenv run python manage.py test
