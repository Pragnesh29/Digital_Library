from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    
    # Books
    path('books/', views.book_list_view, name='book_list'),
    path('books/<int:pk>/', views.book_detail_view, name='book_detail'),
    path('books/upload/', views.book_upload_view, name='book_upload'),
    
    # Articles
    path('articles/', views.article_list_view, name='article_list'),
    path('articles/<int:pk>/', views.article_detail_view, name='article_detail'),
    path('articles/upload/', views.article_upload_view, name='article_upload'),
    
    # User Upload Status Dashboard
    path('dashboard/', views.user_dashboard_view, name='user_dashboard'),
    path('cancel/<str:content_type>/<int:pk>/', views.cancel_upload_view, name='cancel_upload'),
    
    # Faculty / Super Admin Dashboards
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-dashboard/approve-user/<int:user_id>/', views.approve_user_view, name='approve_user'),
    path('admin-dashboard/approve-book/<int:book_id>/', views.approve_book_view, name='approve_book'),
    path('admin-dashboard/approve-article/<int:article_id>/', views.approve_article_view, name='approve_article'),
    path('admin-dashboard/toggle-highlight/<str:content_type>/<int:pk>/', views.toggle_highlight_view, name='toggle_highlight'),
]
