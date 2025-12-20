from django.contrib import admin
from .models import Lesson, LessonMedia, LessonProgress


class LessonMediaInline(admin.TabularInline):
    model = LessonMedia
    extra = 1
    fields = ['title', 'file', 'file_type', 'description']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['module', 'title', 'order', 'duration_minutes', 'is_published', 'is_free', 'created_at']
    list_filter = ['module__course', 'is_published', 'is_free', 'created_at']
    search_fields = ['title', 'content']
    inlines = [LessonMediaInline]
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Основна інформація', {
            'fields': ('module', 'title', 'order')
        }),
        ('Контент', {
            'fields': ('content', 'video_url', 'duration_minutes')
        }),
        ('Налаштування', {
            'fields': ('is_published', 'is_free')
        }),
        ('Дати', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(LessonMedia)
class LessonMediaAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'title', 'file_type', 'get_file_size_display', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['title', 'description']


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'is_completed', 'completed_at', 'time_spent']
    list_filter = ['is_completed', 'completed_at']
    search_fields = ['student__username', 'lesson__title']