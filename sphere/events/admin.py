from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'sort_order', 'category', 'image_thumbnail', 'pub_date')
    list_editable = ('sort_order',)
    search_fields = ('name', 'short_description', 'description')
    empty_value_display = '-пусто-'
    list_filter = ('is_published', 'pub_date', 'category')
    fieldsets = (
        ('Программа', {'fields': ('name', 'slug', 'category', 'sort_order', 'is_published')}),
        ('Публичный каталог', {
            'fields': ('image', 'slogan', 'short_description'),
            'description': 'Эту информацию видят все посетители сайта.',
        }),
        ('Что входит в концепцию', {
            'fields': ('scenario', 'interactives', 'host', 'actors', 'music', 'props'),
        }),
        ('Формат мероприятия', {'fields': ('program_format', 'timing', 'dress_code')}),
        ('Только для сотрудников', {'fields': ('description',)}),
    )

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
