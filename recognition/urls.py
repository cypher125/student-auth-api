from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecognitionViewSet

router = DefaultRouter()
router.register(r'', RecognitionViewSet, basename='recognition')

urlpatterns = [
    path('', include(router.urls)),
] 