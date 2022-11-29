from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from django.core.mail import send_mail
from django.db.models import Count  # позволяет выполнять агрегирующий запрос для подсчета количества тегов
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

from django.contrib.postgres.search import TrigramSimilarity

from .forms import EmailPostForm, CommentForm, SearchForm
from .models import Post, Comment
from taggit.models import Tag


def post_list(request, tag_slug=None):
    """Функция вывода всех статьей """
    object_list = Post.published.all()  # обращаемся к собственному менеджеру
    tag = None

    if tag_slug:  # Если передали таги
        tag = get_object_or_404(Tag, slug=tag_slug)  # Ищем теги
        object_list = object_list.filter(tags__in=[tag])  # фильтруем записи по тегам

    paginator = Paginator(object_list, 3)  # три записи на страницу
    page = request.GET.get('page')  # Получаем из request номер страницы или None

    try:
        posts = paginator.page(page)  # получаем список объектов на нужной странице
    except PageNotAnInteger:  # Если страница не целое число (None)...
        posts = paginator.page(1)  # возвращаем страницу номер 1
    except EmptyPage:  # Если номер страницы больше, чем количество страниц ...
        posts = paginator.page(paginator.num_pages)  # возвращаем последнюю
    return render(request, 'blog/post/list.html', {'page': page, 'posts': posts, 'tag': tag})


class PostListView(ListView):
    queryset = Post.published.all()  # не использовали model для того что бы использовать свой менеджер модели
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_detail(request, year, month, day, post):
    """Функция отображения статьи детально"""
    post = get_object_or_404(
        Post,
        slug=post,
        status='published',
        publish__year=year,
        publish__month=month,
        publish__day=day
    )
    comments = post.comments.filter(active=True)  # related_name = comments , активные комментарии
    new_comment = None
    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)  # создаем комментарий, но не сохраняем в БД для ...
            new_comment.post = post  # привязки комментария к текущей статье
            new_comment.save()
    else:
        comment_form = CommentForm()

    post_tags_ids = post.tags.values_list('id', flat=True)  # из post получаем id всех тегов, values_list = извлекает
    # из модели только те поля которые указаны и возвращает кортежи, flat используем для вывода значение как в списке

    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)  # получаем статьи у которых
    # есть такие же теги, exclude убирает текущую статью

    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
    # annotate = делает агрегатное вычисление, Count = количество объекта, same_tags = ???

    return render(request, 'blog/post/detail.html', {
        'post': post,
        'comments': comments,
        'new_comment': new_comment,
        'comment_form': comment_form,
        'similar_posts': similar_posts
    })


def post_share(request, post_id):
    """Функция отправки уведомлений"""
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False

    if request.method == "POST":
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f'{cd["name"]} ({cd["email"]}) recommends you reading "{post.title}"'
            message = f"Read '{post.title}' at {post_url}\n\n {cd['name']}\'s comments:\n {cd['comments']}"
            send_mail(subject, message, 'admin@myblog.com', [cd['to']])
            sent = True

    else:  # если форма не валидна ...
        form = EmailPostForm()  # возвращаем форму с веденными данными
    # TODO: Не обновляется страница при отправки сообщения
    return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'send': sent})


# def post_search(request):
#     """ Функция поиска
#         оставил что бы видеть разные способы реализации
#     """
#     form = SearchForm()
#     query = None
#     results = []
#     if 'query' in request.GET:  # если GET содержит query...
#         form = SearchForm(request.GET)  # переопределяем form, добавляя в форму данные которые ищутся
#         if form.is_valid():
#           query = form.cleaned_data['query']
#
#           search_vector = SearchVector('title', weight='A') + SearchVector('body', weight='B')  # повышаю значимость
#           # совпадение в заголовке, что бы заголовки были в больший приоритет чем совпадение в статье
#
#           search_query = SearchQuery(query)  # преобразует фразы в объект поиска, использует алгоритм Стемминга
#
#           results = Post.objects.annotate(
#               search=search_vector,
#               rank=SearchRank(search_vector, search_query)  # SearchRank ранжирует статьи
#           ).filter(rank__gte=0.3).order_by('-rank')  # rank__gte = Отбрасываем статьи с низким рангом. Поиск и
#           # сортировка по rank
#     context = {
#         'form': form,
#         'query': query,
#         'results': results,
#     }
#     return render(request, 'blog/post/search.html', context=context)
def post_search(request):
    """ Функция поиска
        установи расширение pg_trgm
    """
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:  # если GET содержит query...
        form = SearchForm(request.GET)  # переопределяем form, добавляя в форму данные которые ищутся
        if form.is_valid():
            query = form.cleaned_data['query']
            results = Post.objects.annotate(
                similarity=TrigramSimilarity('title', 'query'),
            ).filter(similarity__gte=0.3).order_by(
                '-similarity')  # rank__gte = Отбрасываем статьи с низким рангом. Поиск и
            # сортировка по rank

    return render(
        request,
        'blog/post/search.html',
        {'form': form,
         'query': query,
         'results': results, }
    )
