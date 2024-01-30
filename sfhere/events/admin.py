from django.contrib import admin

from .models import Event, Category


from django.utils.html import format_html

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'slug', 'description', 'pub_date', 'category', 'image_thumbnail')
    search_fields = ('description',)
    empty_value_display = '-пусто-'
    list_filter = ('pub_date', 'category')

    def image_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />'.format(obj.image.url))
        else:
            return '-'

    image_thumbnail.short_description = 'Изображение'

# @admin.register(Event)
# class EventAdmin(admin.ModelAdmin):
#     list_display = ('pk', 'name', 'description', 'pub_date', 'category')
#     search_fields = ('description',)
#     empty_value_display = '-пусто-'
#     list_filter = ('pub_date', 'category')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'slug')