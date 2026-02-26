from django.urls import path
from . import views

app_name = 'recurring'

urlpatterns = [
    path('', views.recurring_list, name='list'),
    path('new/', views.recurring_create, name='create'),
    path('<uuid:pk>/toggle/', views.recurring_toggle, name='toggle'),
    path('<uuid:pk>/delete/', views.recurring_delete, name='delete'),
]
