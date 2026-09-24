from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Department, Group

class UserSignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="Full Name")
    email = forms.EmailField(required=True, label="Email Address")
    contact_no = forms.CharField(max_length=15, required=True, label="Contact Number")
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=True, label="Division/Department")
    group = forms.ModelChoiceField(queryset=Group.objects.all(), required=True, label="Group")

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('first_name', 'email', 'contact_no', 'department', 'group')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply CSS classes for premium glassmorphism form styling
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = f'Enter {field.label}'

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username', '').strip()
        email = cleaned_data.get('email', '').strip()
        contact_no = cleaned_data.get('contact_no', '').strip()

        email_exists = False
        contact_exists = False
        username_exists = False

        if email and CustomUser.objects.filter(email__iexact=email).exists():
            email_exists = True

        if contact_no and CustomUser.objects.filter(contact_no=contact_no).exists():
            contact_exists = True

        if username and CustomUser.objects.filter(username__iexact=username).exists():
            username_exists = True

        if email_exists and contact_exists:
            msg = f"Email ID '{email}' and Mobile No '{contact_no}' are already used. Kindly contact administrator."
            self.add_error('email', msg)
            self.add_error('contact_no', msg)
            raise forms.ValidationError(msg)
        elif email_exists:
            msg = f"Email ID '{email}' is already used. Kindly contact administrator."
            self.add_error('email', msg)
            raise forms.ValidationError(msg)
        elif contact_exists:
            msg = f"Mobile No '{contact_no}' is already used. Kindly contact administrator."
            self.add_error('contact_no', msg)
            raise forms.ValidationError(msg)
        elif username_exists:
            msg = f"Username '{username}' is already used. Kindly contact administrator."
            self.add_error('username', msg)
            raise forms.ValidationError(msg)

        return cleaned_data
