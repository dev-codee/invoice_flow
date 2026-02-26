from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('invoice/<uuid:invoice_pk>/record/', views.record_payment, name='record'),
    path('invoice/<uuid:invoice_pk>/stripe/', views.stripe_checkout, name='stripe_checkout'),
    path('invoice/<uuid:invoice_pk>/stripe/success/', views.stripe_success, name='stripe_success'),
]
