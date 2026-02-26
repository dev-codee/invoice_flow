from django.urls import path
from . import views

app_name = 'organizations'

urlpatterns = [
    path('settings/', views.org_settings, name='settings'),
    path('invite/', views.invite_member, name='invite'),
    path('invite/accept/<uuid:token>/', views.accept_invitation, name='accept_invite'),
    path('members/<int:pk>/remove/', views.remove_member, name='remove_member'),
]
