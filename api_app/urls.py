from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'clients', views.ClientViewSet, basename='client')
router.register(r'invoices', views.InvoiceViewSet, basename='invoice')
router.register(r'payments', views.PaymentViewSet, basename='payment')

app_name = 'api_app'

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    path('auth/token/', views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    path('reports/revenue/', views.RevenueReportView.as_view(), name='revenue_report'),
    path('reports/aging/', views.AgingReportView.as_view(), name='aging_report'),
]
