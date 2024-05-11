from django import forms

from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event

        fields = ('text', 'group', )
        fields = ['name', 'slug', 'description', 'category', 'image']
        # labels = {
        #     'text': 'Введите текст',
        #     'group': 'Выберите группу'
        # }

        # help_texts = {
        #     'text': 'Текст нового поста',
        #     'group': 'Группа, к которой будет относиться пост',
        # }