compose-up:
	docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

compose-down:
	docker-compose down

compose-enter:
	docker-compose exec app bash -c "cd /workspace; source .venv/bin/activate; exec zsh"

runserver:
	python manage.py runserver 0.0.0.0:8000

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations
