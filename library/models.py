from django.db import models
from accounts.models import CustomUser, Department, Group

class Book(models.Model):
    title = models.CharField(max_length=200)
    pdf = models.FileField(upload_to='books/pdfs/')
    cover_image = models.ImageField(upload_to='books/covers/', blank=True, null=True)
    category_tag = models.CharField(max_length=50)
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='uploaded_books')
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
