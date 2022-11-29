import markdown
from django import template
from django.db.models import Count
from django.utils.safestring import mark_safe

from ..models import Post

register = template.Library()  # для регистрации тегов


@register.simple_tag  # Обраб. данные и возвращает строку
def total_posts():
    """ Возвращает количество опуб. статьей"""
    return Post.published.count()


@register.inclusion_tag('blog/post/latest_posts.html')  # Обраб. данные и возвращает фрагмент шаблона
def show_latest_posts(count=5):
    """ Возвращает последние опубликованные записи"""
    latest_posts = Post.published.order_by('-publish')[:count]
    return {'latest_posts': latest_posts}


@register.simple_tag  # Обраб. данные и возвращает строку
def get_most_commented_posts(count=5):
    """Отображение статьи с наибольшим количеством комментариев """
    return Post.published.annotate(total_comments=Count('comments')).order_by('-total_comments')[:count]
    # агрегатное вычисление по группам записей используем annotate


@register.filter(name='markdown')
def markdown_format(text):
    return mark_safe(
        markdown.markdown(text))  # mark_save = что бы html кот выполнится, по умолчанию django не доверяет HTML
