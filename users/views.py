from django.shortcuts import render
from rest_framework import viewsets, status, generics, views
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from .models import Student, Admin, User
from .serializers import (
    StudentSerializer, AdminSerializer,
    UserSerializer, LoginSerializer
)
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

# Add new view to list all users
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_all_users(request):
    """
    List all users (both students and admins).
    
    Only accessible to admin users.
    """
    # Check if the user is an admin
    if not hasattr(request.user, 'admin_profile'):
        return Response(
            {'error': 'You don\'t have permission to view all users'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get all students and their data
    students = Student.objects.all()
    student_data = StudentSerializer(students, many=True).data
    for student in student_data:
        student['role'] = 'student'
    
    # Get all admins and their data
    admins = Admin.objects.all()
    admin_data = AdminSerializer(admins, many=True).data
    for admin in admin_data:
        admin['role'] = 'admin'
    
    # Combine the data
    all_users = student_data + admin_data
    
    return Response(all_users)

class StudentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing student resources.
    
    This viewset provides CRUD operations for students, as well as a special
    endpoint to retrieve the current user's student profile.
    
    Permissions:
    - List/Retrieve: Authentication required
    - Create: Open to all (for student registration)
    - Update/Delete: Authentication required
    """
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Set permission based on action.
        
        Returns:
            list: Permission classes for the current action
        """
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """
        Get the student profile of the currently authenticated user.
        
        Returns:
            Response: The student profile data
        
        Status Codes:
            200: Success
            404: Student profile not found
        """
        try:
            student = request.user.student_profile
            serializer = self.get_serializer(student)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            
    def update(self, request, *args, **kwargs):
        """
        Update a student record.
        
        This method handles both PUT and PATCH requests for updating 
        student information. It includes proper error handling and
        appropriate status codes.
        
        Returns:
            Response: The updated student data or error message
            
        Status Codes:
            200: Success
            400: Invalid request data
            404: Student not found
        """
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}
                
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
    def destroy(self, request, *args, **kwargs):
        """
        Delete a student record and the associated user account.
        
        This method handles DELETE requests for removing both the student record
        and the associated user account to ensure complete removal from the system.
        
        Returns:
            Response: Success message or error message
            
        Status Codes:
            204: Success (No Content)
            404: Student not found
            500: Server error during deletion
        """
        try:
            instance = self.get_object()
            user = instance.user  # Get the user associated with this student
            
            # Use a transaction to ensure both student and user are deleted together
            with transaction.atomic():
                # Delete the student first
                self.perform_destroy(instance)
                
                # Then delete the associated user
                user.delete()
                
            return Response(
                {'message': 'Student and associated user account deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error deleting student and user: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AdminViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing admin resources.
    
    This viewset provides CRUD operations for administrators, as well as a special
    endpoint to retrieve the current user's admin profile.
    
    Permissions:
    - List/Retrieve: Authentication required
    - Create: Open to all (for admin registration)
    - Update/Delete: Authentication required
    """
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Set permission based on action.
        
        Returns:
            list: Permission classes for the current action
        """
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """
        Get the admin profile of the currently authenticated user.
        
        Returns:
            Response: The admin profile data
        
        Status Codes:
            200: Success
            404: Admin profile not found
        """
        try:
            admin = request.user.admin_profile
            serializer = self.get_serializer(admin)
            return Response(serializer.data)
        except Admin.DoesNotExist:
            return Response(
                {'error': 'Admin profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class LoginView(generics.GenericAPIView):
    """
    API endpoint for user authentication.
    
    This view handles both admin and student login, using different
    credentials for each role.
    
    Admin login: email and password
    Student login: matric number and surname
    
    Returns JWT tokens (access and refresh) upon successful authentication.
    """
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Authenticate a user and return JWT tokens.
        
        Args:
            request: HTTP request
            
        Returns:
            Response: Contains tokens and user data on success
        
        Request Body:
            {
                "role": "admin|student",
                // For admin login
                "email": "admin@example.com",
                "password": "password",
                // For student login
                "matric_number": "MAT123456",
                "surname": "Doe"
            }
        
        Response Body:
            {
                "token": "access_token",
                "refresh": "refresh_token",
                "user": { ... }
            }
        
        Status Codes:
            200: Success
            400: Invalid request data
            401: Invalid credentials
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        role = serializer.validated_data['role']

        if role == 'student':
            matric_number = serializer.validated_data['matric_number']
            surname = serializer.validated_data['surname']
            try:
                # Find student by matric number and verify surname
                student = Student.objects.get(matric_number=matric_number)
                if student.last_name.lower() != surname.lower():
                    return Response(
                        {'error': 'Invalid credentials'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                user = student.user
                profile = student
                profile_serializer = StudentSerializer
            except Student.DoesNotExist:
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        else:
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            # Authenticate admin using email and password
            user = authenticate(email=email, password=password)
            if not user or not user.is_staff:
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            try:
                profile = user.admin_profile
                profile_serializer = AdminSerializer
            except Admin.DoesNotExist:
                return Response(
                    {'error': 'Admin profile not found'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'token': str(refresh.access_token),
            'refresh': str(refresh),
            'user': profile_serializer(profile).data
        })

class CreateStudentWithUserView(views.APIView):
    """
    API view to create a new student and user in one operation.
    This endpoint allows admins to create a student account by automatically creating
    the user account first, then linking it to a new student profile.
    
    This view also supports uploading a face image for the student.
    """
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Add support for form data and file uploads

    @transaction.atomic
    def post(self, request):
        try:
            # Extract user data from request
            email = request.data.get('email')
            password = request.data.get('password')
            first_name = request.data.get('firstName')
            last_name = request.data.get('lastName')
            
            # Student specific data
            matric_number = request.data.get('matricNumber')
            faculty = request.data.get('faculty')
            department = request.data.get('department')
            level = request.data.get('level')
            course = request.data.get('course', '')
            grade = request.data.get('grade', '')
            
            # Get face image file if provided
            face_image = request.FILES.get('faceImage')
            
            # Validate required fields
            if not all([email, password, first_name, last_name, matric_number, department, level]):
                return Response(
                    {"error": "Missing required fields"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the User instance first
            user = User.objects.create_user(
                email=email,
                password=password,
            )
            
            # Then create the associated Student
            student = Student.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                matric_number=matric_number,
                department=department,
                class_year=level,
                faculty=faculty or department,  # Default faculty to department if not provided
                course=course,
                grade=grade,
            )
            
            # Add face image if provided
            if face_image:
                student.face_image = face_image
                student.save()
            
            # Return the created student
            serializer = StudentSerializer(student)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # Rollback happens automatically due to @transaction.atomic
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CreateAdminWithUserView(views.APIView):
    """
    API view to create a new admin and user in one operation.
    This endpoint allows admins to create another admin account by automatically creating
    the user account first, then linking it to a new admin profile.
    """
    permission_classes = [IsAdminUser]

    @transaction.atomic
    def post(self, request):
        try:
            # Extract user data from request
            email = request.data.get('email')
            password = request.data.get('password')
            first_name = request.data.get('firstName')
            last_name = request.data.get('lastName')
            
            # Admin specific data
            department = request.data.get('department')
            faculty = request.data.get('faculty', '')  # Get faculty if provided
            username = request.data.get('username', email)  # Default to email if not provided
            
            # Validate required fields
            if not all([email, password, first_name, last_name, department]):
                return Response(
                    {"error": "Missing required fields"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the User instance first with is_staff=True
            user = User.objects.create_user(
                email=email,
                password=password,
                is_staff=True,  # This indicates an admin user
            )
            
            # Then create the associated Admin
            admin = Admin.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                username=username,
                faculty=faculty or department,  # Use provided faculty or fall back to department
            )
            
            # Return the created admin
            serializer = AdminSerializer(admin)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # Rollback happens automatically due to @transaction.atomic
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
