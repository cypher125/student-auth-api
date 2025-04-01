from django.contrib import admin
from .models import RecognitionLog

class RecognitionLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'timestamp', 'confidence', 'success')
    list_filter = ('success', 'timestamp')
    search_fields = ('student__first_name', 'student__last_name', 'student__matric_number')
    readonly_fields = ('id', 'timestamp', 'student', 'confidence', 'success', 'image')
    
    fieldsets = (
        ('Recognition Details', {
            'fields': ('id', 'student', 'timestamp', 'confidence', 'success')
        }),
        ('Image Data', {
            'fields': ('image',),
            'classes': ('collapse',),
        }),
    )
    
    def has_add_permission(self, request):
        # Prevent adding records manually as they should only be created by the recognition system
        return False
    
    def has_change_permission(self, request, obj=None):
        # Prevent editing logs for integrity
        return False

# Register RecognitionLog model
admin.site.register(RecognitionLog, RecognitionLogAdmin)
