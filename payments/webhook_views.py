# Re-export the real webhook handler so webhook_urls.py resolves correctly.
from .views import stripe_webhook  # noqa: F401
