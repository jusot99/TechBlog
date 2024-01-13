from django.shortcuts import render, get_object_or_404, redirect
from .models import Article, Category, User, Profile, Comment, UserStatistics, Notification
from django.contrib.auth import login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError


class CustomUserCreationForm(UserCreationForm):
    """
    Custom registration form with email and password validation.
    """
    email = forms.EmailField(required=True, label='Email')

    def clean_password1(self):
        """
        Validate the length of the password.
        """
        password = self.cleaned_data.get("password1")
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters.")
        return password

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom login form.
    """
    class Meta:
        model = User
        fields = ['username', 'password']


class ContactForm(forms.Form):
    """
    Custom contact form.
    """
    subject = forms.CharField(max_length=100, label='Subject')
    message = forms.CharField(widget=forms.Textarea, label='Your Message')
    sender_email = forms.EmailField(label='Your Email')

class ProfileUpdateForm(forms.ModelForm):
    """
    Form for updating user profile information.
    """
    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'photo', 'email', 'gender']

    def __init__(self, *args, **kwargs):
        """
        Initialize the form and pre-populate the email field with the user's email.
        """
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.fields['email'].initial = self.instance.user.email if self.instance.user.email else ''

    def clean_email(self):
        """
        Validate and update the user's email if it has changed.
        """
        email = self.cleaned_data.get('email')
        if email and email != self.instance.user.email:
            user = self.instance.user
            user.email = email
            user.save()
        return email

class CommentForm(forms.ModelForm):
    """
    Form for adding comments to an article.
    """
    class Meta:
        model = Comment
        fields = ['content']

def index(request):
    """
    View for rendering the index page.
    """
    featured_articles = Article.objects.filter(is_featured=True)[:3]
    context = {"featured_articles": featured_articles}
    return render(request, 'index.html', context)

def articles(request):
    """
    View for rendering the articles page.
    """
    all_articles = Article.objects.all()
    context = {"all_articles": all_articles}
    return render(request, 'articles.html', context)

def categories(request):
    """
    View for rendering the categories page.
    """
    all_categories = Category.objects.all()
    context = {"all_categories": all_categories}
    return render(request, 'categories.html', context)

def view_articles_by_category(request, category_slug):
    """
    View for rendering articles based on a specific category.
    """
    category = get_object_or_404(Category, slug=category_slug)
    articles = Article.objects.filter(categories=category)
    return render(request, 'view_articles_by_category.html', {'category': category, 'articles': articles})

def about(request):
    """
    View for rendering the about page.
    """
    return render(request, 'about.html')

@login_required(login_url='/login')
def bookmark_article(request, article_id):
    """
    View for bookmarking an article.
    """
    article = get_object_or_404(Article, id=article_id)
    request.user.profile.saved_articles.add(article)
    messages.success(request, 'Article bookmarked successfully.')
    return redirect('article_detail', slug=article.slug)

def article_detail(request, slug):
    """
    View for rendering the detail page of an article.
    """
    article = get_object_or_404(Article, slug=slug)
    comments = article.comments.all()
    context = {"article": article, "comments": comments}

    if request.user.is_authenticated:
        try:
            user_statistics = UserStatistics.objects.get(user=request.user)
        except UserStatistics.DoesNotExist:
            user_statistics = UserStatistics.objects.create(user=request.user)
            
        user_statistics.articles_read += 1
        user_statistics.save()

        if request.user != article.author:
            Notification.objects.create(
                user=article.author,
                article=article,
                message=f"{request.user.username} read your article: {article.title}"
            )

    return render(request, 'article_detail.html', context)

@login_required(login_url='/login')
def notifications(request):
    """
    View for rendering the notifications page.
    """
    user_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': user_notifications})

@login_required(login_url='/login')
def like_article(request, article_id):
    """
    View for liking an article.
    """
    article = get_object_or_404(Article, id=article_id)
    user = request.user

    if article.likes.filter(id=user.id).exists():
        article.likes.remove(user)
        user_statistics = UserStatistics.objects.get(user=user)
        user_statistics.likes_given -= 1
        user_statistics.save()
    else:
        article.likes.add(user)
        user_statistics = UserStatistics.objects.get(user=user)
        user_statistics.likes_given += 1
        user_statistics.save()

        if request.user != article.author:
            Notification.objects.create(
                user=article.author,
                article=article,
                message=f"{request.user.username} liked your article: {article.title}"
            )

    return redirect('article_detail', slug=article.slug)

@login_required(login_url='/login')
def unlike_article(request, article_id):
    """
    View for unliking an article.
    """
    article = get_object_or_404(Article, id=article_id)
    user = request.user

    if article.likes.filter(id=user.id).exists():
        article.likes.remove(user)
        user_statistics = UserStatistics.objects.get(user=user)
        user_statistics.likes_given -= 1
        user_statistics.save()

        Notification.objects.filter(
            user=article.author,
            article=article,
            message=f"{request.user.username} liked your article: {article.title}"
        ).delete()

    else:
        article.likes.add(user)
        user_statistics = UserStatistics.objects.get(user=user)
        user_statistics.likes_given += 1
        user_statistics.save()

    return redirect('article_detail', slug=article.slug)

@login_required(login_url='/login')
def add_comment(request, article_id):
    """
    View for adding a comment to an article.
    """
    article = get_object_or_404(Article, id=article_id)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.author = request.user
            comment.article = article
            comment.save()

            try:
                user_statistics = UserStatistics.objects.get(user=request.user)
            except UserStatistics.DoesNotExist:
                user_statistics = UserStatistics.objects.create(user=request.user)

            user_statistics.comments_posted += 1
            user_statistics.save()

            if request.user != article.author:
                Notification.objects.create(
                    user=article.author,
                    article=article,
                    message=f"{request.user.username} commented on your article: {article.title}"
                )

            return redirect('article_detail', slug=article.slug)
    else:
        form = CommentForm()

    context = {'form': form, 'article': article}
    return render(request, 'add_comment.html', context)

def author_detail(request, username):
    """
    View for rendering the detail page of an author.
    """
    author = get_object_or_404(User, username=username)
    author_articles = Article.objects.filter(author=author)
    context = {"author": author, "author_articles": author_articles}
    return render(request, 'author_detail.html', context)

@login_required(login_url='/login')
def dashboard(request):
    """
    View for rendering the dashboard page.
    """
    try:
        user_statistics = UserStatistics.objects.get(user=request.user)
    except ObjectDoesNotExist:
        user_statistics = UserStatistics.objects.create(user=request.user)

    user_articles = Article.objects.filter(author=request.user)
    context = {
        "user_articles": user_articles,
        "user": request.user,
        'user_statistics': user_statistics,
    }

    return render(request, 'dashboard.html', context)

@login_required
def profile(request):
    """
    View for rendering the user profile page.
    """
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile(user=request.user)
        profile.save()

    user_data = {
        'email': request.user.email,
        # Add other fields as needed
    }

    if request.method == 'POST':
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if profile_form.is_valid():
            profile = profile_form.save(commit=False)
            profile.save()

            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Error updating profile. Please correct the errors below.')
    else:
        profile_form = ProfileUpdateForm(instance=profile, initial=user_data)

    return render(request, 'profile.html', {'profile_form': profile_form})

def contact(request):
    """
    View for rendering the contact page and handling contact form submissions.
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            sender_email = form.cleaned_data['sender_email']

            recipient_list = [settings.CONTACT_EMAIL]
            send_mail(subject, message, sender_email, recipient_list)

            messages.success(request, 'Your message has been sent. Thank you!')
            return redirect('contact')
        else:
            messages.error(request, 'Error sending message. Please correct the errors below.')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})

def register(request):
    """
    View for rendering the registration page and handling user registration.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful. You are now logged in.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Registration failed. Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    """
    View for rendering the login page and handling user login.
    """
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Login successful.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Login failed. Please check your username and password.')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'login.html', {'form': form})

def user_logout(request):
    """
    View for handling user logout.
    """
    logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('index')
