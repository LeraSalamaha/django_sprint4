from django.utils import timezone

from .models import Post


def get_published_posts():
    """Views функция возвращает опубликованные посты."""
    return Post.objects.filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    )
