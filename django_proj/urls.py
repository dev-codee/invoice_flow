"""
InvoiceFlow root URL configuration.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth (allauth)
    path('accounts/', include('allauth.urls')),

    # InvoiceFlow app views
    path('', include('dashboard.urls')),
    path('clients/', include('clients.urls')),
    path('invoices/', include('invoices.urls')),
    path('payments/', include('payments.urls')),
    path('organizations/', include('organizations.urls')),
    path('recurring/', include('recurring.urls')),
    path('notifications/', include('notifications.urls')),

    # REST API
    path('api/', include('api_app.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Stripe Webhook (outside /api/ to avoid auth)
    path('webhooks/stripe/', include('payments.webhook_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
