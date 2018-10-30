runserver:
	pipenv run ./manage.py runserver

migrate:
	pipenv run ./manage.py migrate

makemigrations:
	pipenv run ./manage.py makemigrations

superuser:
	pipenv run ./manage.py createsuperuser

scss:
	npm run watch-scss
