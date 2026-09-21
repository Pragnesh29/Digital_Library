from django.contrib import admin
from .models import Category, Book, Article, ArticleImage, ArticleAttachment, AuditLog, Feedback, FeedbackImage

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'target_type', 'created_at')
    list_filter = ('target_type',)
    search_fields = ('name',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'category_tag', 'uploaded_by', 'is_approved', 'is_highlighted', 'created_at')
    list_filter = ('is_approved', 'is_highlighted', 'category')
    search_fields = ('title', 'category_tag')

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'uploaded_by', 'is_approved', 'is_highlighted', 'created_at')
    list_filter = ('is_approved', 'is_highlighted', 'category')
    search_fields = ('title', 'description')

@admin.register(ArticleAttachment)
class ArticleAttachmentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'article', 'created_at')
    search_fields = ('file_name', 'article__title')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp')
    list_filter = ('action',)
    search_fields = ('action', 'details')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('subject', 'user', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('subject', 'message', 'user__username')

@admin.register(FeedbackImage)
class FeedbackImageAdmin(admin.ModelAdmin):
    list_display = ('feedback', 'image', 'created_at')
