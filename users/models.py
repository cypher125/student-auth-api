from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid

class CustomUserManager(BaseUserManager):
    """
    Custom manager for the User model that provides methods for creating
    users and superusers with email as the unique identifier.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user with an email and password.
        
        Args:
            email (str): User's email address (must be unique)
            password (str, optional): User's password
            **extra_fields: Additional fields to be saved in the user model
            
        Returns:
            User: The created user instance
            
        Raises:
            ValueError: If email is not provided
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with admin privileges.
        
        Args:
            email (str): User's email address (must be unique)
            password (str, optional): User's password
            **extra_fields: Additional fields to be saved in the user model
            
        Returns:
            User: The created superuser instance
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model that uses email instead of username for authentication.
    
    This model extends Django's AbstractBaseUser and PermissionsMixin to 
    provide a fully featured user model with admin-compliant permissions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Add custom related_name for these fields
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        related_name='custom_user_set',
        help_text='The groups this user belongs to.'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        related_name='custom_user_permission_set',
        help_text='Specific permissions for this user.'
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

class Student(models.Model):
    """
    Student model that represents a student in the system.
    
    This model contains academic information and is linked to a User model
    for authentication details. It also stores the student's face image
    for facial recognition.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    matric_number = models.CharField(max_length=20, unique=True)
    faculty = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    class_year = models.CharField(max_length=50)
    course = models.CharField(max_length=100)
    grade = models.CharField(max_length=10)
    face_image = models.ImageField(upload_to='student_faces/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.matric_number})"

    class Meta:
        ordering = ['last_name', 'first_name']

class Admin(models.Model):
    """
    Admin model that represents an administrator in the system.
    
    This model contains administrative information and is linked to a User model
    with is_staff=True for enhanced permissions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    username = models.CharField(max_length=50, unique=True)
    faculty = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'admin'
        verbose_name_plural = 'admins'
