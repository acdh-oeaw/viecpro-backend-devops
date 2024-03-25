
# commands used in development

run: 
	python manage.py runserver

test: 
	python manage.py test

notebook:
	python manage.py shell_plus --notebook

makemigrations: 
	python manage.py makemigrations

migrate:
	python manage.py migrate

full-migrate: makemigrations migrate

worker:
	celery -A apis worker -l info 
	

clear-solid-assets:
	cd deduplication_tool/static/deduplication_tool && rm -r ./assets

solid-build:
	cd deduplication_tool/solid_app && npm run build 

solid-copy:
	cd deduplication_tool/solid_app && cp -r ./dist/static/deduplication_tool/assets ../static/deduplication_tool/ && cp  ./dist/solid_app.html ../templates/deduplication_tool/solid_app.html

solid: clear-solid-assets solid-build solid-copy