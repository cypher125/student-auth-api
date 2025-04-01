from rest_framework import serializers
from .models import User, Student, Admin

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    
    This serializer provides read-only access to basic user information.
    """
    class Meta:
        model = User
        fields = ('id', 'email', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class StudentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Student model.
    
    This serializer handles CRUD operations for students, including
    nested creation and update of the associated User model.
    """
    email = serializers.EmailField(source='user.email', read_only=True)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Student
        fields = (
            'id', 'first_name', 'last_name', 'email', 'password',
            'matric_number', 'faculty', 'department', 'class_year',
            'course', 'grade', 'face_image'
        )
        read_only_fields = ('id',)

    def create(self, validated_data):
        """
        Create a new Student with associated User.
        
        This method extracts User-related data from the validated data,
        creates a User instance, and then creates a Student instance
        associated with that User.
        
        Args:
            validated_data (dict): Validated data from the request
            
        Returns:
            Student: The created Student instance
        """
        user_data = {
            'email': validated_data.pop('user')['email'],
            'password': validated_data.pop('password', None)
        }
        
        user = User.objects.create_user(
            email=user_data['email'],
            password=user_data['password']
        )
        
        student = Student.objects.create(user=user, **validated_data)
        return student

    def update(self, instance, validated_data):
        """
        Update a Student and its associated User.
        
        This method updates both the Student instance and its associated
        User instance if user data is provided.
        
        Args:
            instance (Student): The Student instance to update
            validated_data (dict): Validated data from the request
            
        Returns:
            Student: The updated Student instance
        """
        if 'user' in validated_data:
            user_data = validated_data.pop('user')
            user = instance.user
            
            if 'email' in user_data:
                user.email = user_data['email']
                user.save()

        return super().update(instance, validated_data)

class AdminSerializer(serializers.ModelSerializer):
    """
    Serializer for the Admin model.
    
    This serializer handles CRUD operations for admins, including
    nested creation and update of the associated User model.
    """
    email = serializers.EmailField(source='user.email', read_only=True)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Admin
        fields = (
            'id', 'first_name', 'last_name', 'username',
            'faculty', 'email', 'password'
        )
        read_only_fields = ('id',)

    def create(self, validated_data):
        """
        Create a new Admin with associated User.
        
        This method extracts User-related data from the validated data,
        creates a User instance with is_staff=True, and then creates an Admin 
        instance associated with that User.
        
        Args:
            validated_data (dict): Validated data from the request
            
        Returns:
            Admin: The created Admin instance
        """
        user_data = {
            'email': validated_data.pop('user')['email'],
            'password': validated_data.pop('password', None)
        }
        
        user = User.objects.create_user(
            email=user_data['email'],
            password=user_data['password'],
            is_staff=True
        )
        
        admin = Admin.objects.create(user=user, **validated_data)
        return admin

    def update(self, instance, validated_data):
        """
        Update an Admin and its associated User.
        
        This method updates both the Admin instance and its associated
        User instance if user data is provided.
        
        Args:
            instance (Admin): The Admin instance to update
            validated_data (dict): Validated data from the request
            
        Returns:
            Admin: The updated Admin instance
        """
        if 'user' in validated_data:
            user_data = validated_data.pop('user')
            user = instance.user
            
            if 'email' in user_data:
                user.email = user_data['email']
                user.save()

        return super().update(instance, validated_data)

class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    
    This serializer handles two login methods:
    1. Admin login with email and password
    2. Student login with matric number and surname
    """
    role = serializers.ChoiceField(choices=['admin', 'student'])
    
    # For admin login
    email = serializers.EmailField(required=False)
    password = serializers.CharField(required=False)
    
    # For student login
    matric_number = serializers.CharField(required=False)
    surname = serializers.CharField(required=False)

    def validate(self, data):
        """
        Validate login credentials based on role.
        
        Ensures that the appropriate fields are provided based on login role.
        
        Args:
            data (dict): The data to validate
            
        Returns:
            dict: The validated data
            
        Raises:
            ValidationError: If required fields for a role are missing
        """
        role = data.get('role')
        
        if role == 'admin':
            if not data.get('email'):
                raise serializers.ValidationError({'email': 'Email is required for admin login'})
            if not data.get('password'):
                raise serializers.ValidationError({'password': 'Password is required for admin login'})
        
        if role == 'student':
            if not data.get('matric_number'):
                raise serializers.ValidationError({'matric_number': 'Matric number is required for student login'})
            if not data.get('surname'):
                raise serializers.ValidationError({'surname': 'Surname is required for student login'})
        
        return data 