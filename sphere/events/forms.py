from django import forms

from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event

        fields = ['name', 'slug', 'description', 'category', 'image']
        labels = {
            'name': 'Название',
            'slug': 'Slug',
            'description': 'Описание',
            'category': 'Категория',
            'image': 'Изображение'
        }

        help_texts = {
            'name': 'Введите название мероприятия',
            'slug': 'Введите название мероприятия латинскими буквами',
            'description': 'Введите описание мероприятия',
            'category': 'Выберите категорию',
            'image': 'Загрузите изображение'
        }
