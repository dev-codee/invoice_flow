from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.client_list, name='list'),
    path('new/', views.client_create, name='create'),
    path('<uuid:pk>/', views.client_detail, name='detail'),
    path('<uuid:pk>/edit/', views.client_update, name='update'),
    path('<uuid:pk>/delete/', views.client_delete, name='delete'),
    path('import/', views.client_import_csv, name='import_csv'),
]
