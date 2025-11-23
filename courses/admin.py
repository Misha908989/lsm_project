from django.contrib import admin
from .models import Course, Module, Enrollment, Announcement

# Register your models here.
class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1
    fields = ['title', 'description', 'order']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'instructor', 'level', 'is_published', 'created_at']
    list_filter = ['level', 'is_published', 'created_at']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ModuleInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['course', 'title', 'order', 'created_at']
    list_filter = ['course', 'created_at']
    search_fields = ['title', 'description']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'is_active', 'progress', 'enrolled_at']
    list_filter = ['is_active', 'enrolled_at']
    search_fields = ['student__username', 'course__title']


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'type', 'course', 'is_active', 'is_pinned', 'created_at']
    list_filter = ['type', 'is_active', 'is_pinned', 'created_at']
    search_fields = ['title', 'content']