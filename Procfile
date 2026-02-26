web: gunicorn django_proj.wsgi:application
worker: celery -A django_proj worker --loglevel=info
beat: celery -A django_proj beat --loglevel=info