from django import forms

from .models import Event


class EventForm(forms.ModelForm):
    field_groups = (
        ('Программа', ('name', 'slug', 'category', 'sort_order', 'is_published')),
        ('Публичный каталог', ('image', 'slogan', 'short_description')),
        ('Что входит в концепцию', (
            'scenario', 'interactives', 'host', 'actors', 'music', 'props',
        )),
        ('Формат мероприятия', ('program_format', 'timing', 'dress_code')),
        ('Только для сотрудников', ('description',)),
    )

    @property
    def sections(self):
        return [(title, [self[name] for name in names])
                for title, names in self.field_groups]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Missing order in an older form submission keeps its previous behavior.
        self.fields['sort_order'].required = False

    def clean_sort_order(self):
        value = self.cleaned_data.get('sort_order')
        return self.instance.sort_order if value is None else value

    class Meta:
        model = Event

        fields = [
            'name', 'slug', 'category', 'sort_order', 'is_published', 'image', 'slogan',
            'short_description', 'scenario', 'interactives', 'host', 'actors',
            'music', 'props', 'program_format', 'timing', 'dress_code', 'description',
        ]
        labels = {
            'name': 'Название',
            'slug': 'Slug',
            'description': 'Полное описание для сотрудников',
            'category': 'Категория',
            'image': 'Изображение'
        }

        help_texts = {
            'name': 'Введите название мероприятия',
            'slug': 'Введите название мероприятия латинскими буквами',
            'description': 'Внутренняя информация. Доступна только после входа.',
            'short_description': 'Описание программы, которое видят потенциальные клиенты.',
            'slogan': 'Короткая подпись внутри иллюстрации.',
            'sort_order': 'Меньшее число — выше в каталоге. Номер рассчитывается автоматически.',
            'category': 'Выберите категорию',
            'image': 'Загрузите изображение'
        }

        widgets = {
            name: forms.Textarea(attrs={'rows': 2})
            for name in (
                'scenario', 'interactives', 'host', 'actors', 'music', 'props',
                'program_format', 'timing', 'dress_code',
            )
        }
        widgets['short_description'] = forms.Textarea(attrs={'rows': 5})
