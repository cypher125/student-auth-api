from django.db import models
from users.models import Student
import uuid

class RecognitionLog(models.Model):
    """
    Recognition Log model to store face recognition attempts.
    
    This model records each facial recognition attempt, whether successful or not,
    along with confidence score and reference to the identified student (if any).
    The captured image is stored for audit purposes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    confidence = models.FloatField()
    success = models.BooleanField(default=False)
    image = models.ImageField(upload_to='recognition_logs/', null=True)
    processing_time = models.FloatField(null=True, blank=True, help_text="Recognition processing time in seconds")
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.student} - {self.timestamp} - {'Success' if self.success else 'Failed'}"
