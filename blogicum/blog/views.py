"""Views функция для blog."""
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone

from .forms import PostForm, UserProfileForm, CommentForm
from .models import Category, Post, Comment
from .utils import get_published_posts, paginate_queryset

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

    if post.author != request.user:
        post = get_object_or_404(
            Post.objects.filter(
                is_published=True,
                pub_date__lte=timezone.now(),
                category__is_published=True,
            ),
            pk=post_id
        )

    comments = Comment.objects.filter(post=post)
    form = CommentForm()

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect('blog:post_detail', post_id=post.id)

    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }

    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    """Views функция для вывода постов выбранной категории."""
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )

    post_list = get_published_posts().filter(category=category)
    page_obj = paginate_queryset(request, post_list, LIMIT_POSTS_COUNT)

    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'blog/category.html', context)


@login_required
def create_post(request):
    form = PostForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user

        post.is_published = post.pub_date <= timezone.now()

        post.save()
        profile_url = reverse(
            'blog:profile',
            kwargs={'username': request.user.username}
        )

        return redirect(profile_url)

    return render(request, 'blog/create.html', {'form': form})


def profile_view(request, username):
    """Views функция для отображения профиля автора."""
    profile = get_object_or_404(User, username=username)

    posts = (
        Post.objects
        .filter(author=profile)
        .annotate(comment_count=Count('comment'))
        .order_by('-pub_date')
    )

    page_obj = paginate_queryset(request, posts, LIMIT_POSTS_COUNT)

    return render(
        request,
        'blog/profile.html',
        {
            'profile': profile,
            'page_obj': page_obj
        }
    )


@login_required
def edit_profile(request):
    user = request.user
    form = UserProfileForm(request.POST or None, instance=user)

    if form.is_valid():
        form.save()
        return redirect('blog:profile', username=user.username)

    return render(request, 'blog/user.html', {'form': form})


def logout_view(request):
    logout(request)
    return render(request, 'registration/logged_out.html')


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post.id)

    form = PostForm(request.POST or None, request.FILES or None, instance=post)

    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post.id)

    return render(request, 'blog/create.html', {'form': form, 'post': post})


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post.id)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)

    return render(request, 'blog/create.html', {'post': post})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect('blog:post_detail', post_id=post.id)

    comments = post.comments.all().order_by('created_at')
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'blog/comment.html', context)


@login_required
def edit_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user:
        return HttpResponseForbidden(
            "Вы не имеете прав для редактирования этого комментария."
        )

    form = CommentForm(request.POST or None, instance=comment)

    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post.id)

    comments = post.comment.all().order_by('created_at')

    return render(request, 'blog/comment.html', {
        'comment': comment,
        'post': post,
        'comments': comments,
        'form': form
    })


@login_required
def delete_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user:
        return HttpResponseForbidden(
            "Вы не имеете прав для удаления этого комментария."
        )

    if request.method == 'POST':
        comment.delete()
        return redirect(
            reverse_lazy(
                'blog:post_detail',
                kwargs={'post_id': post.id}
            )
        )
    return render(request, 'blog/comment.html', {'comment': comment})
