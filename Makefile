
# commands used in development

run: 
	python manage.py runserver

test: 
	python manage.py test

shell: 
	python manage.py shell_plus 
	
notebook:
	python manage.py shell_plus --notebook

makemigrations: 
	python manage.py makemigrations

migrate:
	python manage.py migrate

full-migrate: makemigrations migrate

worker:
	celery -A apis worker -l info 
	