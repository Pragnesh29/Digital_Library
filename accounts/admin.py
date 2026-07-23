from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Department, Group

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'contact_no', 'department', 'group', 'role', 'is_approved', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('contact_no', 'department', 'group', 'role', 'is_approved')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('email', 'contact_no', 'department', 'group', 'role', 'is_approved')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Department)
admin.site.register(Group)
