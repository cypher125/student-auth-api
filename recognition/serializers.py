from rest_framework import serializers
from .models import RecognitionLog
from users.serializers import StudentSerializer

class RecognitionLogSerializer(serializers.ModelSerializer):
    """
    Serializer for RecognitionLog model.
    
    Provides detailed information about facial recognition attempts,
    including the associated student information.
    """
    student = StudentSerializer(read_only=True)
    
    class Meta:
        model = RecognitionLog
        fields = ('id', 'student', 'timestamp', 'confidence', 'success')
        read_only_fields = ('id', 'timestamp')

class FaceRecognitionSerializer(serializers.Serializer):
    """
    Serializer for face recognition requests.
    
    Handles the validation of face image uploads for recognition.
    """
    image = serializers.ImageField()

class FaceRegistrationSerializer(serializers.Serializer):
    """
    Serializer for face registration requests.
    
    Handles the validation of face image uploads and student ID for registration.
    """
    image = serializers.ImageField()
    student_id = serializers.UUIDField() 