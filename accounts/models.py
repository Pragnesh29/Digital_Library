from django.db import models
from django.contrib.auth.models import AbstractUser

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Group(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'Standard User'),
        ('faculty', 'Faculty Approver'),
        ('superuser', 'Super Admin'),
    )
    
    contact_no = models.CharField(max_length=15, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    is_approved = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')

    def save(self, *args, **kwargs):
        # Automatically approve superusers and faculty if created via createsuperuser
        if self.is_superuser:
            self.is_approved = True
            self.role = 'superuser'
        elif self.role == 'superuser':
            self.is_superuser = True
            self.is_staff = True
            self.is_approved = True
        elif self.role == 'faculty':
            self.is_staff = True # Allow faculty to log into django admin if desired
            # Faculty might still need to be approved if signed up, but standard is auto-approve if created by admin
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
