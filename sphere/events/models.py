from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from pytils.translit import slugify

User = get_user_model()


class Event(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name='Слаг')
    description = models.TextField(max_length=400, verbose_name='Описание')
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')
    category = models.ForeignKey(
        'Category',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='cats', verbose_name='Категория'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='events/',
        blank=True
    )

    class Meta:
        verbose_name = 'объект «Мероприятие»'
        verbose_name_plural = 'Мероприятия'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('events:event_detail', kwargs={"slug": self.slug})
    
    def save(self, *args, **kwargs):
        if not self.slug:
            max_slug_length = self._meta.get_field('slug').max_length
            self.slug = slugify(self.name)[:max_slug_length]
        super().save(*args, **kwargs)


class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(unique=True, verbose_name='Слаг')

    class Meta:
        verbose_name = 'объект «Категория»'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('events:category_events', kwargs={"cat_slug": self.slug})
