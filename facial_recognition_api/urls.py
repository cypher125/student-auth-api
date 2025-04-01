"""
Facial Recognition System API URL Configuration

This module configures all API endpoint URLs for the facial recognition system,
including user authentication, student management, admin management, and 
facial recognition operations.

The URL patterns include:
- Admin interface (/admin/)
- API root with browsable interface
- Authentication endpoints (login, token refresh)
- Student management
- Admin user management
- Face recognition and registration (available at both /api/recognition/ and /api/users/recognition/ for compatibility)
- API documentation (Swagger/OpenAPI)
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.urls import direct_patterns as users_direct_patterns
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from .views import home

# Configure Swagger/OpenAPI documentation
schema_view = get_schema_view(
   openapi.Info(
      title="Yabatech Facial Recognition API",
      default_version='v1',
      description="API for the Yabatech Facial Recognition System",
      terms_of_service="https://www.yabatech.edu.ng/terms/",
      contact=openapi.Contact(email="admin@yabatech.edu.ng"),
      license=openapi.License(name="Yabatech License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Home page
    path('', home, name='home'),
    
    # Admin site
    path('admin/', admin.site.urls),
    
    # API endpoint includes
    path('api/users/', include('users.urls')),
    path('api/recognition/', include('recognition.urls')),
    
    # Direct paths from app modules
    path('api/', include(users_direct_patterns)),
    
    # Swagger documentation
    path('api/schema/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-docs'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
