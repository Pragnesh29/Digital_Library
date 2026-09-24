from django.db import models
from accounts.models import CustomUser, Department, Group

class Category(models.Model):
    TARGET_CHOICES = (
        ('both', 'Both (Books & Articles)'),
        ('book', 'Books Only'),
        ('article', 'Articles Only'),
    )
    name = models.CharField(max_length=100, unique=True)
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES, default='both')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


STATUS_CHOICES = (
    ('pending', 'Pending Approval'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
)

class Book(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True, verbose_name="Description / Summary")
    pdf = models.FileField(upload_to='books/pdfs/')
    cover_image = models.ImageField(upload_to='books/covers/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    category_tag = models.CharField(max_length=50, blank=True)
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='uploaded_books')
    show_uploader = models.BooleanField(default=True, verbose_name="Show Uploader Name")
    is_approved = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_remark = models.TextField(blank=True, null=True)
    is_highlighted = models.BooleanField(default=False)
    
    # Specific departments or groups that can view this book (blank means all logged-in users can view)
    restricted_to_departments = models.ManyToManyField(Department, blank=True, related_name='restricted_books')
    restricted_to_groups = models.ManyToManyField(Group, blank=True, related_name='restricted_books')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def get_category_name(self):
        if self.category:
            return self.category.name
        return self.category_tag or "General"

    def __str__(self):
        return self.title

class Article(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='uploaded_articles')
    show_uploader = models.BooleanField(default=True, verbose_name="Show Uploader Name")
    is_approved = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_remark = models.TextField(blank=True, null=True)
    is_highlighted = models.BooleanField(default=False)
    
    # Specific departments or groups that can view this article (blank means all logged-in users can view)
    restricted_to_departments = models.ManyToManyField(Department, blank=True, related_name='restricted_articles')
    restricted_to_groups = models.ManyToManyField(Group, blank=True, related_name='restricted_articles')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def get_category_name(self):
        if self.category:
            return self.category.name
        return "General"

    def non_image_attachments(self):
        return [att for att in self.attachments.all() if not att.is_image()]

    def non_image_attachments_count(self):
        return len(self.non_image_attachments())

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
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.user} - {self.action}"


class Feedback(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
        ('ignored', 'N/A'),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='feedbacks')
    subject = models.CharField(max_length=200)
    message = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback by {self.user.username}: {self.subject}"


class FeedbackImage(models.Model):
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='feedback_images/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for feedback {self.feedback.id}"
