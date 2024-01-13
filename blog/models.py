from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse

class Category(models.Model):
    """
    Represents a category for articles.

    Attributes:
        name (str): The name of the category.
        slug (str): A slugified version of the name for use in URLs.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Saves the category and generates a slug if not provided.
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Article(models.Model):
    """
    Represents an article.

    Attributes:
        title (str): The title of the article.
        slug (str): A slugified version of the title for use in URLs.
        author (User): The author of the article (linked to the User model).
        content (str): The content of the article.
        categories (ManyToManyField): Categories associated with the article.
        pub_date (DateTimeField): The publication date of the article.
        updated_at (DateTimeField): The last update date of the article.
        is_featured (bool): Indicates if the article is featured.
        likes (ManyToManyField): Users who liked the article.
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    categories = models.ManyToManyField(Category)
    pub_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)
    likes = models.ManyToManyField(User, related_name='liked_articles', blank=True)

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Saves the article, generates a slug if not provided.
        """
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Returns the absolute URL of the article.
        """
        return reverse('article_detail', args=[str(self.id)])

class Comment(models.Model):
    """
    Represents a comment on an article.

    Attributes:
        article (Article): The article to which the comment belongs.
        author (User): The author of the comment (linked to the User model).
        content (str): The content of the comment.
        pub_date (DateTimeField): The publication date of the comment.
    """
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['pub_date']

    def __str__(self):
        return f'Comment by {self.author} on {self.article}'

class Profile(models.Model):
    """
    Represents a user profile.

    Attributes:
        user (User): The user associated with the profile.
        saved_articles (ManyToManyField): Articles bookmarked by the user.
        first_name (str): The first name of the user.
        last_name (str): The last name of the user.
        email (str): The email address of the user.
        photo (ImageField): Image data for the user's photo.
        gender (str): The gender of the user.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    saved_articles = models.ManyToManyField('Article', related_name='bookmarked_by', blank=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    email = models.EmailField(max_length=254, blank=True)
    photo = models.ImageField(upload_to='theme/static/images/', blank=True, null=True)
    gender_choices = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=gender_choices, blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'

class UserStatistics(models.Model):
    """
    Represents user statistics.

    Attributes:
        user (User): The user associated with the statistics.
        articles_read (int): The number of articles read by the user.
        comments_posted (int): The number of comments posted by the user.
        likes_given (int): The number of likes given by the user.
        article (Article): The last article associated with the user statistics.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    articles_read = models.IntegerField(default=0)
    comments_posted = models.IntegerField(default=0)
    likes_given = models.IntegerField(default=0)
    article = models.ForeignKey(Article, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f'Statistics for {self.user.username}'

class Notification(models.Model):
    """
    Represents a notification for a user.

    Attributes:
        user (User): The user receiving the notification.
        article (Article): The article associated with the notification.
        message (str): The content of the notification message.
        created_at (DateTimeField): The creation date of the notification.
        is_read (bool): Indicates if the notification has been read.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.article.title} - {self.created_at}"
