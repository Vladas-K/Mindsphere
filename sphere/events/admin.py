from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Event
from .forms import EventForm
from .ordering import catalog_position, save_at_position


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    form = EventForm
    list_display = ('name', 'catalog_position', 'category', 'image_thumbnail', 'pub_date')
    search_fields = ('name', 'short_description', 'description')
    empty_value_display = '-пусто-'
    list_filter = ('is_published', 'pub_date', 'category')
    fieldsets = (
        ('Программа', {'fields': ('name', 'slug', 'category', 'sort_order', 'is_published')}),
        ('Публичный каталог', {
            'fields': ('image', 'number_color', 'slogan', 'short_description'),
            'description': 'Эту информацию видят все посетители сайта.',
        }),
        ('Что входит в концепцию', {
            'fields': ('scenario', 'interactives', 'host', 'actors', 'music', 'props'),
        }),
        ('Формат мероприятия', {'fields': ('program_format', 'timing', 'dress_code')}),
        ('Только для сотрудников', {'fields': ('description',)}),
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if request.user.is_superuser:
            return fieldsets
        return tuple((title, {**options, 'fields': tuple(
            name for name in options['fields'] if name != 'slogan'
        )}) for title, options in fieldsets)

    def get_form(self, request, obj=None, **kwargs):
        base_form = super().get_form(request, obj, **kwargs)

        class UserEventForm(base_form):
            def __init__(self, *args, **form_kwargs):
                form_kwargs['user'] = request.user
                super().__init__(*args, **form_kwargs)

        return UserEventForm

    @admin.display(description='Позиция в каталоге', ordering='sort_order')
    def catalog_position(self, obj):
        return catalog_position(obj)

    def save_model(self, request, obj, form, change):
        save_at_position(obj)

    def image_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" />', obj.image.url)
        else:
            return '-'

    image_thumbnail.short_description = 'Изображение'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
