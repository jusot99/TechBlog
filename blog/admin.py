from django.contrib import admin
from .models import Article, Category, Comment, Profile, UserStatistics, Notification

class CategoryInline(admin.TabularInline):
    """
    Inline for managing categories associated with an article in the ArticleAdmin.
    """
    model = Article.categories.through

class CommentInline(admin.TabularInline):
    """
    Inline for managing comments associated with an article in the ArticleAdmin.
    """
    model = Comment
    extra = 1

class UserStatisticsInline(admin.StackedInline):
    """
    Inline for managing user statistics associated with a user in the UserAdmin.
    """
    model = UserStatistics

class ArticleAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Article model.
    """
    list_per_page = 20
    list_display = ('title', 'author', 'pub_date', 'is_featured', 'categories_list')
    list_filter = ('categories', 'pub_date')
    search_fields = ('title', 'content')
    inlines = [CategoryInline, CommentInline, UserStatisticsInline]

    def categories_list(self, obj):
        """
        Display the list of categories associated with an article in the admin.
        """
        return ", ".join([category.name for category in obj.categories.all()])
    categories_list.short_description = 'Categories'

    def comments_list(self, obj):
        """
        Display the list of comments associated with an article in the admin.
        """
        return ", ".join([comment.author.username for comment in obj.comments.all()])
    comments_list.short_description = 'Comments'

admin.site.register(Article, ArticleAdmin)
admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(Profile)
admin.site.register(UserStatistics)

class NotificationAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Notification model.
    """
    list_per_page = 20
    list_display = ('user', 'article', 'message', 'created_at', 'is_read')
    list_filter = ('user', 'is_read')
    search_fields = ('user__username', 'message')
    readonly_fields = ('created_at',)

admin.site.register(Notification, NotificationAdmin)
