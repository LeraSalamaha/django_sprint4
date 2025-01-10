"""Views функция для blog."""
from django.shortcuts import render, redirect, get_object_or_404

from .models import Category, Post, Comments
from django.contrib.auth.models import User
from .forms import PostForm, UserProfileForm, CommentForm
from .utils import get_published_posts
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import HttpResponseForbidden
from django import forms
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Count
from django.urls import reverse_lazy
LIMIT_POSTS_COUNT = 10


def get_published_posts():
    return Post.objects.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).annotate(comment_count=Count('comment')).order_by('-pub_date')


def index(request):
    """Views функция для главной страницы."""
    post_list = get_published_posts()
    paginator = Paginator(post_list, LIMIT_POSTS_COUNT)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }

    return render(request, 'blog/index.html', context)


def post_detail(request, post_id):
    """Views функция для детализации постов."""
    post = get_object_or_404(Post, pk=post_id)

    # Проверка на то, опубликован ли пост
    if not post.is_published:
        # Если пост не опубликован и пользователь не автор, возвращаем 404
        if post.author != request.user:
            return render(request, 'pages/404.html', status=404)

    # Проверка на то, опубликована ли категория поста
    if post.category and not post.category.is_published:
        if post.author != request.user:
            return render(request, 'pages/404.html', status=404)

    # Если пост отложен, проверяем, является ли пользователь автором
    if post.pub_date > timezone.now():
        if post.author != request.user:
            # Если не автор, возвращаем 404
            return render(request, 'pages/404.html', status=404)

    comments = Comments.objects.filter(post=post)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = CommentForm()

    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }

    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    """Views функция для вывода постов выбранной категории."""
    category = get_object_or_404(Category,
                                 slug=category_slug,
                                 is_published=True)

    # Получаем опубликованные посты для выбранной категории
    post_list = get_published_posts().filter(category=category)
    paginator = Paginator(post_list, LIMIT_POSTS_COUNT)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'blog/category.html', context)


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user  # Устанавливаем автора поста

            # Проверка на отложенную публикацию
            if post.pub_date > timezone.now():
                post.is_published = False  # Устанавливаем не опубликованный
            else:
                post.is_published = True  # дата в прошлом, публикуем пост

            post.save()
            return redirect(f'/profile/{request.user.username}/')
    else:
        form = PostForm()

    return render(request, 'blog/create.html', {'form': form})


def profile_view(request, username):
    """Views функция для отображения профиля автора."""
    profile = get_object_or_404(User, username=username)
    # Получаем посты автора, отсортированные от новых к старым
    posts = (
        Post.objects
        .filter(author=profile)
        .annotate(comment_count=Count('comment'))
        .order_by('-pub_date')
    )
    paginator = Paginator(posts, LIMIT_POSTS_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request,
                  'blog/profile.html',
                  {'profile': profile, 'page_obj': page_obj})


@login_required
def edit_profile(request):
    user = request.user  # Получаем текущего пользователя
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=user.username)
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'blog/user.html', {'form': form})


def logout_view(request):
    logout(request)
    return render(request, 'registration/logged_out.html')


@login_required
def edit_post(request, id):
    post = get_object_or_404(Post, id=id)

    # Проверка, является ли пользователь автором поста 403
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post.id)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = PostForm(instance=post)

    return render(request, 'blog/create.html', {'form': form, 'post': post})


@login_required
def post_delete(request, id):
    post = get_object_or_404(Post, id=id)

    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post.id)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)
    else:
        return render(request, 'blog/create.html', {'post': post})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = CommentForm()

    comments = post.comments.all().order_by('created_at')
    return render(request,
                  'blog/comment.html',
                  {'post': post, 'form': form, 'comment': comments})


@login_required
def edit_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comments, id=comment_id)

    # Проверка, является ли пользователь автором комментария
    if comment.author != request.user:
        return HttpResponseForbidden(
            "Вы не имеете прав для редактирования этого комментария."
        )

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = CommentForm(instance=comment)

    # Получите все комментарии для поста
    comments = post.comment.all().order_by('created_at')

    # Возвращаем страницу с формой редактирования комментария
    return render(request, 'blog/comment.html', {
        'comment': comment,
        'post': post,
        'comments': comments,
        'form': form
    })


#   Определяем пустую форму для подтверждения удаления
class ConfirmationForm(forms.Form):
    pass


@login_required
def delete_comment(request, post_id, comment_id):
    # Получаем пост и комментарий
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comments, id=comment_id)

    # Проверка, является ли пользователь автором комментария
    if comment.author != request.user:
        return HttpResponseForbidden(
            "Вы не имеете прав для удаления этого комментария."
        )

    if request.method == 'POST':
        # Удаляем комментарий
        comment.delete()
        # Используем reverse_lazy для перенаправления на страницу поста
        return redirect(
            reverse_lazy(
                'blog:post_detail',
                kwargs={'post_id': post.id}
            )
        )

    # Если не POST, можно, отобразить страницу с подтверждением удаления
    return render(request, 'blog/comment.html', {'comment': comment})
