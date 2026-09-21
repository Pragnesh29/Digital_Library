from django.db import models
from accounts.models import CustomUser, Department, Group

class Book(models.Model):
    title = models.CharField(max_length=200)
    pdf = models.FileField(upload_to='books/pdfs/')
    cover_image = models.ImageField(upload_to='books/covers/', blank=True, null=True)
    category_tag = models.CharField(max_length=50)
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='uploaded_books')
    show_uploader = models.BooleanField(default=True, verbose_name="Show Uploader Name")
    is_approved = models.BooleanField(default=False)
    is_highlighted = models.BooleanField(default=False)
    
    # Specific departments or groups that can view this book (blank means all logged-in users can view)
    restricted_to_departments = models.ManyToManyField(Department, blank=True, related_name='restricted_books')
    restricted_to_groups = models.ManyToManyField(Group, blank=True, related_name='restricted_books')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Article(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='uploaded_articles')
    show_uploader = models.BooleanField(default=True, verbose_name="Show Uploader Name")
    is_approved = models.BooleanField(default=False)
    is_highlighted = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ArticleImage(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='articles/images/')

    def __str__(self):
        return f"Image for {self.article.title}"


class ArticleAttachment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='articles/attachments/')
    file_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_image(self):
        name = self.file_name or self.file.name
        ext = name.split('.')[-1].lower()
        return ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg']

    def is_pdf(self):
        name = self.file_name or self.file.name
        return name.lower().endswith('.pdf')

    def is_doc(self):
        name = self.file_name or self.file.name
        ext = name.split('.')[-1].lower()
        return ext in ['doc', 'docx', 'txt', 'rtf', 'odt', 'csv', 'xls', 'xlsx', 'ppt', 'pptx']

    def file_extension(self):
        name = self.file_name or self.file.name
        return name.split('.')[-1].upper()

    def __str__(self):
        return f"Attachment {self.file_name or self.file.name} for {self.article.title}"


class AuditLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=255)
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} at {self.timestamp}"
