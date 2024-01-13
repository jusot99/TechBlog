from django.urls import path
from .views import (
    index, register, user_login, user_logout, bookmark_article, like_article,
    articles, categories, view_articles_by_category, about, contact, unlike_article,
    dashboard, profile, article_detail, author_detail, add_comment, notifications
)

urlpatterns = [
    path('', index, name='index'),
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('articles/', articles, name='articles'),
    path('categories/', categories, name='categories'),
    path('categories/<slug:category_slug>/', view_articles_by_category, name='view_articles_by_category'),
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('dashboard/', dashboard, name='dashboard'),
    path('profile/', profile, name='profile'),
    path('article/<slug:slug>/', article_detail, name='article_detail'),
    path('add_comment/<int:article_id>/', add_comment, name='add_comment'),
    path('author/<str:username>/', author_detail, name='author_detail'),
    path('notifications/', notifications, name='notifications'),
    path('bookmark/<int:article_id>/', bookmark_article, name='bookmark_article'),
    path('like/<int:article_id>/', like_article, name='like_article'),
    path('unlike/<int:article_id>/', unlike_article, name='unlike_article'),
    # Add more paths for other views as needed
]