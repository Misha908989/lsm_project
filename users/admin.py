from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile
from django.utils.html import format_html

# Register your models here.
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name = 'Профіль'
    fields = ['bio', 'avatar', 'phone', 'role']


class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined', 'profile__role']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    
    def get_role(self, obj):
        """Отримати роль з кольоровим значком"""
        role_colors = {
            'admin': 'danger',
            'teacher': 'success',
            'student': 'info'
        }
        role = obj.profile.role
        color = role_colors.get(role, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.profile.get_role_display()
        )
    get_role.short_description = 'Роль'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_email', 'role', 'phone', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    readonly_fields = ['created_at']
    actions = ['make_teacher', 'make_student']
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    
    def make_teacher(self, request, queryset):
        """Зробити викладачами"""
        updated = queryset.update(role='teacher')
        self.message_user(request, f'{updated} користувачів стали викладачами')
    make_teacher.short_description = 'Зробити викладачами'
    
    def make_student(self, request, queryset):
        """Зробити студентами"""
        updated = queryset.update(role='student')
        self.message_user(request, f'{updated} користувачів стали студентами')
    make_student.short_description = 'Зробити студентами'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.site_header = "LMS - Адміністрування"
admin.site.site_title = "LMS Admin"
admin.site.index_title = "Панель управління"