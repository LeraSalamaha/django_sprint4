from django.db.models import Count
from django.utils import timezone
from django.core.paginator import Paginator

from .models import Post


def get_published_posts():
    """Views функция возвращает опубликованные посты."""
    return Post.objects.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).annotate(comment_count=Count('comment')).order_by('-pub_date')


def paginate_queryset(request, queryset, limit):
    paginator = Paginator(queryset, limit)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
