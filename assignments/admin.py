from django.contrib import admin
from .models import Assignment, Submission, Grade, Certificate


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'title', 'max_score', 'due_date', 'get_submission_count', 'created_at']
    list_filter = ['lesson__module__course', 'due_date', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_submission_count(self, obj):
        return obj.get_submission_count()
    get_submission_count.short_description = 'Здач'


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'assignment', 'status', 'is_late', 'submitted_at']
    list_filter = ['status', 'submitted_at']
    search_fields = ['student__username', 'assignment__title']
    readonly_fields = ['submitted_at', 'updated_at']


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['submission', 'teacher', 'score', 'get_percentage', 'get_letter_grade', 'graded_at']
    list_filter = ['graded_at']
    search_fields = ['submission__student__username']
    readonly_fields = ['graded_at']
    
    def get_percentage(self, obj):
        return f'{obj.get_percentage()}%'
    get_percentage.short_description = 'Відсоток'
    
    def get_letter_grade(self, obj):
        return obj.get_letter_grade()
    get_letter_grade.short_description = 'Оцінка'


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_id', 'student', 'course', 'issued_at']
    list_filter = ['issued_at']
    search_fields = ['certificate_id', 'student__username', 'course__title']
    readonly_fields = ['certificate_id', 'issued_at']