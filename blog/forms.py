from django import forms
from .models import Comment


class EmailPostForm(forms.Form):
    """Функция отправки уведомлений"""
    name = forms.CharField(max_length=25)
    email = forms.EmailField()
    to = forms.EmailField()
    comments = forms.CharField(required=False, widget=forms.Textarea)  # widget = для изменения виджета


class CommentForm(forms.ModelForm):
    """Функция комментария"""
    class Meta:
        model = Comment
        fields = ('name', 'email', 'body')  # явно указываем какие поля использовать


class SearchForm(forms.Form):
    """Функция поиска"""
    query = forms.CharField()

