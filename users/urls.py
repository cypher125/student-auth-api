from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    StudentViewSet, AdminViewSet, LoginView, list_all_users, 
    CreateStudentWithUserView, CreateAdminWithUserView
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view
from rest_framework.response import Response

router = DefaultRouter()
router.register(r'students', StudentViewSet)
router.register(r'admins', AdminViewSet)

# Document the list_all_users endpoint for Swagger
list_all_users = swagger_auto_schema(
    method='get',
    operation_description="Get a list of all users (both students and admins)",
    responses={
        200: openapi.Response(
            description="List of all users",
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_STRING, description='User ID'),
                        'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                        'role': openapi.Schema(type=openapi.TYPE_STRING, description='User role (admin or student)'),
                        'faculty': openapi.Schema(type=openapi.TYPE_STRING),
                        'department': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            )
        ),
        401: openapi.Response(description="Authentication credentials were not provided"),
        403: openapi.Response(description="You don't have permission to view all users"),
    },
    tags=['Users']
)(list_all_users)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('all-users/', list_all_users, name='list_all_users'),
    path('register-student/', CreateStudentWithUserView.as_view(), name='register_student'),
    path('register-admin/', CreateAdminWithUserView.as_view(), name='register_admin'),
]

# Create a separate direct endpoint for the all-users URL
@api_view(['GET'])
def direct_all_users(request):
    """
    Direct route for all-users that will be included at project root level
    """
    return list_all_users(request)

# To be included separately in the main urls.py
direct_patterns = [
    path('all-users/', direct_all_users, name='direct_all_users'),
] 