from django.contrib import admin

from .models import Event, Category

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'description', 'pub_date', 'category')
    search_fields = ('description',)
    empty_value_display = '-пусто-'
    list_filter = ('pub_date', 'category')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'slug')