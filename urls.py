"""Project URL Configuration"""
from django.urls import path, include
from users.views import list_all_users

urlpatterns = [
    # Include the app-specific URLs
    path('api/users/', include('users.urls')),
    path('api/recognition/', include('recognition.urls')),
    
    # Add the users list endpoint directly at the root
    path('api/all-users/', list_all_users, name='root_list_all_users'),
] 