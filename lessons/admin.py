from django.contrib import admin
from .models import Lesson, LessonMedia

# Register your models here.
class LessonMediaInline(admin.TabularInline):
    model = LessonMedia
    extra = 1


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['module', 'title', 'order', 'duration_minutes', 'is_published', 'created_at']
    list_filter = ['module__course', 'is_published', 'created_at']
    search_fields = ['title', 'content']
    inlines = [LessonMediaInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LessonMedia)
class LessonMediaAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'file_type', 'title', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['title', 'description']