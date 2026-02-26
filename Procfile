web: gunicorn invoiceflow.wsgi:application
worker: celery -A invoiceflow worker --loglevel=info
beat: celery -A invoiceflow beat --loglevel=info