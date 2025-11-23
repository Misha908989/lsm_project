from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile

# Register your models here.
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name = 'Профіль'


class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff']
    
    def get_role(self, obj):
        return obj.profile.get_role_display()
    get_role.short_description = 'Роль'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email']


admin.site.unregister(User)
admin.site.register(User, UserAdmin)