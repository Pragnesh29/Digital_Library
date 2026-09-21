from django import forms
from django.db.models import Q
from .models import Book, Article, Category
from accounts.models import Department, Group

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={'multiple': True, 'class': 'form-control'}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return [single_file_clean(data, initial)]

class BookUploadForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=True,
        empty_label="-- Select Category --",
        label="Book Category"
    )
    show_uploader = forms.BooleanField(
        initial=True,
        required=False,
        label="Show 'Uploaded By' name publicly"
    )
    restricted_to_departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Restrict to Specific Departments (Leave empty to make public to all logged-in users)"
    )
    restricted_to_groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Restrict to Specific Groups (Leave empty to make public to all logged-in users)"
    )

    class Meta:
        model = Book
        fields = ['title', 'pdf', 'cover_image', 'category', 'show_uploader', 'restricted_to_departments', 'restricted_to_groups']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(Q(target_type='book') | Q(target_type='both'))
        for name in ['title', 'pdf', 'cover_image', 'category']:
            self.fields[name].widget.attrs['class'] = 'form-control'
            if name != 'category':
                self.fields[name].widget.attrs['placeholder'] = f'Enter {self.fields[name].label}'

class ArticleUploadForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="-- Select Category --",
        label="Article Category"
    )
    show_uploader = forms.BooleanField(
        initial=True,
        required=False,
        label="Show 'Uploaded By' name publicly"
    )
    restricted_to_departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Restrict to Specific Departments (Leave empty to make public to all logged-in users)"
    )
    restricted_to_groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Restrict to Specific Groups (Leave empty to make public to all logged-in users)"
    )
    files = MultipleFileField(
        required=False,
        label="Upload Attachments (Photos, PDFs & Word/Text Docs)"
    )

    class Meta:
        model = Article
        fields = ['title', 'description', 'category', 'show_uploader', 'restricted_to_departments', 'restricted_to_groups', 'files']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(Q(target_type='article') | Q(target_type='both'))
        self.fields['title'].widget.attrs['class'] = 'form-control'
        self.fields['title'].widget.attrs['placeholder'] = 'Enter Article Title'
        
        self.fields['category'].widget.attrs['class'] = 'form-control'
        
        self.fields['description'].widget.attrs['class'] = 'form-control'
        self.fields['description'].widget.attrs['placeholder'] = 'Enter Article Description'
        self.fields['description'].widget.attrs['rows'] = 5

        if 'files' in self.fields:
            self.fields['files'].widget.attrs['accept'] = 'image/*,.pdf,.doc,.docx,.txt,.rtf,.odt,.csv,.xls,.xlsx,.ppt,.pptx'
