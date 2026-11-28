from django import forms

from .catalog import prepare_program
from .models import Event
from .ordering import catalog_position, save_at_position


class EventForm(forms.ModelForm):
    sort_order = forms.IntegerField(
        label='Позиция в каталоге', min_value=1, required=False,
        help_text='1 — первая программа. Остальные сдвинутся автоматически. '
                  'Позиция считается среди опубликованных программ; '
                  'число больше длины списка переместит программу в конец.',
    )
    number_color = forms.ChoiceField(
        label='Цвет номера', choices=Event._meta.get_field('number_color').choices,
        required=False, help_text=Event._meta.get_field('number_color').help_text,
    )
    field_groups = (
        ('Программа', ('name', 'slug', 'category', 'sort_order', 'is_published')),
        ('Публичный каталог', ('image', 'number_color', 'slogan', 'short_description')),
        ('Что входит в концепцию', (
            'scenario', 'interactives', 'host', 'actors', 'music', 'props',
        )),
        ('Формат мероприятия', ('program_format', 'timing', 'dress_code')),
        ('Только для сотрудников', ('description',)),
    )

    @property
    def sections(self):
        return [(title, [self[name] for name in names if name in self.fields])
                for title, names in self.field_groups]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not (user and user.is_authenticated and user.is_superuser):
            self.fields.pop('slogan', None)
        position = catalog_position(self.instance)
        self.initial['sort_order'] = (
            position if position is not None else
            max(1, self.instance.sort_order) if self.instance.pk else
            Event.objects.filter(is_published=True).count() + 1
        )
        if not self.instance.number_color:
            ink = prepare_program(self.instance, None, 0)['art_ink']
            self.initial['number_color'] = 'black' if int(ink[1:3], 16) < 128 else 'white'
        else:
            self.initial.setdefault('number_color', self.instance.number_color)

    def clean_number_color(self):
        return self.cleaned_data.get('number_color') or self.instance.number_color

    def clean_sort_order(self):
        value = self.cleaned_data.get('sort_order')
        return self.initial['sort_order'] if value is None else value

    def save(self, commit=True):
        event = super().save(commit=False)
        if commit:
            save_at_position(event)
            self.save_m2m()
        return event

    class Meta:
        model = Event

        fields = [
            'name', 'slug', 'category', 'sort_order', 'is_published', 'image', 'number_color', 'slogan',
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
            'slogan': 'Поле доступно для изменения только суперпользователю. '
                      'Текст слогана отображается в публичной карточке программы. '
                      'Если слоган уже есть на изображении, оставьте поле пустым.',
            'category': 'Выберите категорию',
            'image': 'Загрузите готовое изображение со встроенным слоганом. Рекомендуем PNG размером '
                     '1200 × 1252 px или изображение с такими же пропорциями. '
                     'Сверху слева оставьте свободное место под номер '
                     '(примерно 220 × 200 px). Номер и скруглённые углы добавит сайт.'
        }

        widgets = {
            name: forms.Textarea(attrs={'rows': 2})
            for name in (
                'scenario', 'interactives', 'host', 'actors', 'music', 'props',
                'program_format', 'timing', 'dress_code',
            )
        }
        widgets['short_description'] = forms.Textarea(attrs={'rows': 5})
