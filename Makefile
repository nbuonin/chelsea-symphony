PY_SENTINAL = .venv/sentinal
JS_SENTINAL = node_modules/sentinal
PIPFILE = Pipfile

$(PY_SENTINAL): $(PIPFILE)
	-rm -rf .venv
	pipenv sync 
	touch $@

$(JS_SENTINAL):
	-rm -rf node_modules
	npm install
	touch $@

clean:
	-rm -rf .venv node_modules

runserver: $(PY_SENTINAL)
	pipenv run ./manage.py runserver

migrate: $(PY_SENTINAL)
	pipenv run ./manage.py migrate

makemigrations: $(PY_SENTINAL)
	pipenv run ./manage.py makemigrations

superuser: $(PY_SENTINAL)
	pipenv run ./manage.py createsuperuser

shell: $(PY_SENTINAL)
	pipenv run ./manage.py shell

test: $(PY_SENTINAL)
	pipenv run ./manage.py test

scss: $(JS_SENTINAL)
	npm run watch-scss

docker-image:
	docker build -t nbuonin/chelsea-symphony-wagtail:`git log -n 1 --pretty="%h"` .

docker-test:
	cd docker && docker-compose up --build --abort-on-container-exit --remove-orphans

docker-push:
	docker push nbuonin/chelsea-symphony-wagtail:`git log -n 1 --pretty="%h"`

.PHONY: clean runserver migrate makemigrations superuser shell test scss docker-image docker-test docker-push
