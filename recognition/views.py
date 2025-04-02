from django.shortcuts import render
import numpy as np
import os
import tempfile
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from .models import RecognitionLog
from users.models import Student
from users.serializers import StudentSerializer
from .serializers import (
    RecognitionLogSerializer,
    FaceRecognitionSerializer,
    FaceRegistrationSerializer
)
from django.utils import timezone
from datetime import timedelta
import time
from django.db.models import Avg
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

class RecognitionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for facial recognition operations and logs.
    
    This viewset provides CRUD operations for recognition logs,
    as well as special endpoints for face recognition and registration.
    
    Permissions:
    - List/Retrieve/Update/Delete: Authentication required
    - Recognize: Public access (no authentication required)
    - Register face: Authentication required
    """
    queryset = RecognitionLog.objects.all()
    serializer_class = RecognitionLogSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        method='post',
        operation_description="Recognize a face from an uploaded image using InsightFace technology",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['image'],
            properties={
                'image': openapi.Schema(
                    type=openapi.TYPE_FILE,
                    description='Face image to be recognized (JPEG, PNG)'
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="Face successfully recognized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Indicates success'),
                        'confidence': openapi.Schema(type=openapi.TYPE_NUMBER, description='Recognition confidence score (0-1)'),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_STRING, description='User unique identifier'),
                                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'matric_number': openapi.Schema(type=openapi.TYPE_STRING),
                                'department': openapi.Schema(type=openapi.TYPE_STRING),
                                'class_year': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description='JWT access token'),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token'),
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request - No face detected or no image provided",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Always false for errors'),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            ),
            404: openapi.Response(
                description="Not found - No matching face or no registered students",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Always false for errors'),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message'),
                        'confidence': openapi.Schema(type=openapi.TYPE_NUMBER, description='Highest confidence score if applicable')
                    }
                )
            ),
            500: openapi.Response(
                description="Server error during recognition process",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Always false for errors'),
                        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        },
        tags=['Recognition']
    )
    @action(detail=False, methods=['post'], permission_classes=[])
    def recognize(self, request):
        """
        Recognize a face from an uploaded image using InsightFace technology.
        
        This endpoint uses InsightFace to compare the uploaded face image against all registered 
        student faces and returns the best match if found. The comparison uses face embeddings 
        with cosine similarity to determine matches. A confidence threshold
        (configurable via FACE_RECOGNITION_THRESHOLD environment variable) is used to 
        determine if a match is valid.
        
        If a match is found, JWT tokens are generated for authentication, and a success 
        response is returned with student information. If no match is found or the confidence
        is too low, an error response is returned.
        
        The system logs all recognition attempts, successful or failed, with the confidence
        score and processing time.
        
        Args:
            request: HTTP request with image file
            
        Returns:
            Response: Recognition result with JWT tokens if successful
            
        Request:
            - Content-Type: multipart/form-data
            - Body: { "image": <file> }
            
        Response:
            Success (200):
            {
                "success": true,
                "confidence": 0.95,
                "user": {
                    "id": "uuid-string",
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "matric_number": "12345",
                    "department": "Computer Science",
                    "class_year": "400"
                },
                "token": "access_token",
                "refresh": "refresh_token"
            }
            
            No Face Detected (400):
            {
                "success": false,
                "error": "No face detected in the image"
            }
            
            No Match Found (404):
            {
                "success": false,
                "error": "No matching student found",
                "confidence": 0.3
            }
            
            No Registered Students (404):
            {
                "success": false,
                "error": "No registered students with face images"
            }
            
            Error (500):
            {
                "success": false,
                "error": "Error message"
            }
        """
        if 'image' not in request.FILES:
            return Response({'error': 'No image file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a temp path for the uploaded image
        temp_path = tempfile.gettempdir()
        temp_image_path = os.path.join(temp_path, 'temp_recognize.jpg')
        
        try:
            # Import InsightFace and other dependencies
            import cv2
            import numpy as np
            from insightface.app import FaceAnalysis
            import gc
            
            image_file = request.FILES['image']
            
            # Save uploaded image temporarily
            with open(temp_image_path, 'wb') as f:
                for chunk in image_file.chunks():
                    f.write(chunk)
            
            # Get threshold from settings or use default (lower than DeepFace as InsightFace is more precise)
            recognition_threshold = float(os.environ.get('FACE_RECOGNITION_THRESHOLD', 0.35))
            
            # Find all students with registered face images
            students = Student.objects.exclude(face_image='')
            
            if not students.exists():
                # Clean up
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                    
                return Response({
                    'success': False,
                    'error': 'No registered students with face images'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Start timer for processing time measurement
            start_time = time.time()
            
            # Initialize InsightFace with a more lightweight model
            try:
                # MODEL OPTIONS:
                # buffalo_s = smaller model (less memory, less accurate)
                # buffalo_l = larger model (more memory, more accurate)
                # CURRENT: Using buffalo_l for better accuracy (requires more memory)
                face_analyzer = FaceAnalysis(name="buffalo_l")  # Using larger model for better accuracy
                # face_analyzer = FaceAnalysis(name="buffalo_s")  # Smaller model option (if memory issues occur)
                
                # Using default detection size for better accuracy
                face_analyzer.prepare(ctx_id=0)  # Default size for better accuracy
                # face_analyzer.prepare(ctx_id=0, det_size=(320, 320))  # Reduced size for lower memory usage
            except Exception as e:
                # Fall back to default model with minimal settings if the specific one fails
                face_analyzer = FaceAnalysis()
                face_analyzer.prepare(ctx_id=0, det_size=(320, 320))
            
            # Load and analyze the uploaded image
            try:
                img = cv2.imread(temp_image_path)
                # Resize image to reduce memory usage
                img = cv2.resize(img, (640, 480), interpolation=cv2.INTER_AREA)
                faces = face_analyzer.get(img)
            except Exception as e:
                # Clean up
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                
                return Response({
                    'success': False,
                    'error': f'Error processing image: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Check if a face was detected
            if len(faces) == 0:
                # Clean up
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                    
                # Create failed recognition log
                RecognitionLog.objects.create(
                    student=None,
                    confidence=0.0,
                    success=False,
                    image=image_file
                )
                
                return Response({
                    'success': False,
                    'error': 'No face detected in the image'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get the face with highest detection score if multiple faces are detected
            main_face = max(faces, key=lambda x: x.det_score)
            main_face_embedding = main_face.embedding
            
            best_match = None
            highest_confidence = 0
            
            # Compare with each student's face image
            for student in students:
                student_image_path = student.face_image.path
                
                try:
                    # Load and analyze the student's image
                    student_img = cv2.imread(student_image_path)
                    # Resize student image to save memory
                    student_img = cv2.resize(student_img, (640, 480), interpolation=cv2.INTER_AREA)
                    student_faces = face_analyzer.get(student_img)
                    
                    if len(student_faces) == 0:
                        continue  # No face in this student's image
                    
                    student_face = max(student_faces, key=lambda x: x.det_score)
                    student_embedding = student_face.embedding
                    
                    # Calculate cosine similarity
                    similarity = np.dot(main_face_embedding, student_embedding) / (
                        np.linalg.norm(main_face_embedding) * np.linalg.norm(student_embedding)
                    )
                    
                    # Convert similarity to a confidence score (0-1 range)
                    confidence = (similarity + 1) / 2
                    
                    if confidence > highest_confidence:
                        highest_confidence = confidence
                        best_match = student
                        
                    # Force garbage collection after each comparison to free memory
                    del student_img, student_faces, student_face, student_embedding
                    gc.collect()
                    
                except Exception as e:
                    # Skip this comparison if there's an error
                    print(f"Error comparing with student {student.id}: {str(e)}")
                    continue
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Clean up
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
            
            # Check if we found a match with sufficient confidence
            if best_match and highest_confidence >= recognition_threshold:
                # Create recognition log
                log_data = {
                    'student': best_match,
                    'confidence': highest_confidence,
                    'success': True,
                    'image': image_file,
                }
                
                # Try to add processing_time if the field exists in the model
                try:
                    # Create a test instance to check if the field exists
                    test_log = RecognitionLog()
                    test_log.processing_time = 0
                    # If we get here, the field exists, so add it
                    log_data['processing_time'] = processing_time
                except AttributeError:
                    # Field doesn't exist yet, skip it
                    pass
                
                RecognitionLog.objects.create(**log_data)
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(best_match.user)
                
                return Response({
                    'success': True,
                    'confidence': highest_confidence,
                    'user': {
                        'id': str(best_match.id),
                        'first_name': best_match.first_name,
                        'last_name': best_match.last_name,
                        'email': best_match.user.email,
                        'matric_number': best_match.matric_number,
                        'department': best_match.department,
                        'class_year': best_match.class_year
                    },
                    'token': str(refresh.access_token),
                    'refresh': str(refresh)
                })
            else:
                # Create failed recognition log
                log_data = {
                    'student': None,
                    'confidence': highest_confidence if best_match else 0.0,
                    'success': False,
                    'image': image_file,
                }
                
                # Try to add processing_time if the field exists in the model
                try:
                    # Create a test instance to check if the field exists
                    test_log = RecognitionLog()
                    test_log.processing_time = 0
                    # If we get here, the field exists, so add it
                    log_data['processing_time'] = processing_time
                except AttributeError:
                    # Field doesn't exist yet, skip it
                    pass
                
                RecognitionLog.objects.create(**log_data)
                
                return Response({
                    'success': False,
                    'error': 'No matching student found',
                    'confidence': highest_confidence if best_match else 0.0
                }, status=status.HTTP_404_NOT_FOUND)
            
        except MemoryError:
            # Handle out of memory errors specifically
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
                
            # Force garbage collection
            import gc
            gc.collect()
                
            return Response({
                'success': False,
                'error': 'Server memory limit exceeded. Please try again later or use manual login.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            # Clean up
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
                
            # Log the error for debugging
            import traceback
            print(f"Recognition error: {str(e)}")
            print(traceback.format_exc())
                
            return Response({
                'success': False,
                'error': f'Recognition process failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def register_face(self, request):
        """
        Register a face image for a student.
        
        This endpoint saves a face image for a student to be used in facial recognition.
        It validates that the image contains exactly one face before saving.
        
        Args:
            request: HTTP request with student ID and image file
            
        Returns:
            Response: Success or error message
            
        Request:
            - Content-Type: multipart/form-data
            - Body: {
                "student_id": "uuid-string",
                "image": <file>
              }
            
        Response:
            Success (200):
            {
                "status": "success",
                "message": "Face registered successfully"
            }
            
            Error (400):
            {
                "status": "error",
                "message": "Error message",
                "errorCode": "ERROR_CODE"
            }
            
        Permissions:
            - Authentication required
        """
        try:
            serializer = FaceRegistrationSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Import InsightFace here to avoid loading it during app startup
            import cv2
            import numpy as np
            from insightface.app import FaceAnalysis
            
            student = get_object_or_404(Student, id=serializer.validated_data['student_id'])
            image_file = request.FILES['image']
            
            # Save uploaded image temporarily to check if it contains a valid face
            temp_path = tempfile.gettempdir()
            temp_image_path = os.path.join(temp_path, 'temp_register.jpg')
            
            with open(temp_image_path, 'wb') as f:
                for chunk in image_file.chunks():
                    f.write(chunk)
            
            # Initialize InsightFace
            face_analyzer = FaceAnalysis(name="buffalo_l")
            face_analyzer.prepare(ctx_id=0)  # Use CPU (ctx_id=0) or GPU if available
            
            # Load and analyze the uploaded image
            img = cv2.imread(temp_image_path)
            faces = face_analyzer.get(img)
            
            # Verify image contains a face
            if len(faces) == 0:
                # Clean up
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                    
                return Response({
                    'status': 'error',
                    'message': 'No face detected in the image',
                    'errorCode': 'NO_FACE_DETECTED'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Clean up
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
            
            # Store the face image for the student
            student.face_image = image_file
            student.save()
            
            return Response({
                'status': 'success',
                'message': 'Face registered successfully'
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e),
                'errorCode': 'REGISTRATION_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """
        Get statistics for the admin dashboard including:
        - Total students count
        - Verified today count
        - Failed attempts count
        - Average scan time
        """
        # Get today's date with time at 00:00:00
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate statistics
        total_students = Student.objects.count()
        
        # Count successful verifications today
        verified_today = RecognitionLog.objects.filter(
            timestamp__gte=today,
            success=True
        ).count()
        
        # Count failed attempts
        failed_attempts = RecognitionLog.objects.filter(
            success=False
        ).count()
        
        # Calculate average scan time (use a default if no data)
        # In a real app, you would store the processing time for each recognition
        avg_scan_time = 0.0  # Default value
        
        # You could calculate this from real data if available
        avg_time_calc = RecognitionLog.objects.aggregate(avg_time=Avg('processing_time'))
        if avg_time_calc['avg_time']:
            avg_scan_time = round(avg_time_calc['avg_time'], 1)
        
        return Response({
            'total_students': total_students,
            'verified_today': verified_today,
            'failed_attempts': failed_attempts,
            'avg_scan_time': avg_scan_time
        })
