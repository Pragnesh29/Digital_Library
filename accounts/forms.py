from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Department, Group

class UserSignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="Full Name")
    email = forms.EmailField(required=True, label="Email Address")
    contact_no = forms.CharField(max_length=15, required=True, label="Contact Number")
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=True, label="Division/Department")
    group = forms.ModelChoiceField(queryset=Group.objects.all(), required=True, label="Group")
    role = forms.ChoiceField(
        choices=[('user', 'Standard User'), ('faculty', 'Faculty Approver')],
        required=True,
        label="Register As"
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('first_name', 'email', 'contact_no', 'department', 'group', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply CSS classes for premium glassmorphism form styling
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = f'Enter {field.label}'
