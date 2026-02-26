from django.urls import path
from . import webhook_views

urlpatterns = [
    path('', webhook_views.stripe_webhook, name='stripe_webhook'),
]
