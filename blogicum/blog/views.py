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
LIMIT_POSTS_COUNT = 10


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


@login_required
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
            post.save()
            return redirect(f'/profile/{request.user.username}/')
    else:
        form = PostForm()

    return render(request, 'blog/create.html', {'form': form})


def profile_view(request, username):
    profile = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=profile)
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
                  'includes/comments.html',
                  {'post': post, 'form': form, 'comments': comments})


@login_required
def edit_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comments, id=comment_id)
    # Проверка, является ли пользователь автором комментария 403
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post.id)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = CommentForm(instance=comment)

    # Возвращаем страницу с формой редактирования комментария
    return render(request,
                  'blog/create.html',
                  {'form': form, 'post': post, 'comment': comment})


#   Определяем пустую форму для подтверждения удаления
class ConfirmationForm(forms.Form):
    pass


def delete_comment(request, post_id, comment_id):
    # Получаем пост и комментарий
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comments, id=comment_id)

    # Проверка, является ли пользователь автором комментария
    if comment.author != request.user:
        return HttpResponseForbidden(
            "Вы не имеете прав "
            "для удаления этого комментария."
        )
    if request.method == 'POST':
        # Удаляем комментарий и перенаправляем на страницу поста
        comment.delete()
        return redirect('blog:post_detail', post_id=post.id)
