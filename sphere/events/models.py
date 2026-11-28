from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from pytils.translit import slugify

User = get_user_model()


class Event(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name='Слаг')
    slogan = models.CharField('Слоган', max_length=200, blank=True)
    number_color = models.CharField(
        'Цвет номера', max_length=5,
        choices=(('white', 'Белый'), ('black', 'Чёрный')),
        default='white', null=True, blank=True,
        help_text='Выберите цвет, контрастный фону в верхнем левом углу изображения.',
    )
    short_description = models.TextField('Краткое описание для клиентов', blank=True)
    description = models.TextField(verbose_name='Полное описание для сотрудников', blank=True)
    scenario = models.TextField('Сценарий', blank=True)
    interactives = models.TextField('Интерактивы', blank=True)
    host = models.TextField('Ведущий', blank=True)
    actors = models.TextField('Актёры', blank=True)
    music = models.TextField('Музыка', blank=True)
    props = models.TextField('Реквизит', blank=True)
    program_format = models.TextField('Формат', blank=True)
    timing = models.TextField('Тайминг', blank=True)
    dress_code = models.TextField('Образы / дресс-код', blank=True)
    sort_order = models.PositiveIntegerField('Порядок показа', default=0)
    is_published = models.BooleanField('Показывать в каталоге', default=True)
    catalog_page = models.PositiveSmallIntegerField(null=True, blank=True, editable=False)
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
        ordering = ('sort_order', 'pk')
        verbose_name = 'объект «Мероприятие»'
        verbose_name_plural = 'Мероприятия'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('events:event_detail', kwargs={"slug": self.slug})

    @property
    def concept_features(self):
        fields = ('scenario', 'interactives', 'host', 'actors', 'music', 'props')
        return self._public_fields(fields)

    @property
    def format_features(self):
        return self._public_fields(('program_format', 'timing', 'dress_code'))

    def _public_fields(self, fields):
        return [
            (self._meta.get_field(name).verbose_name, getattr(self, name))
            for name in fields if getattr(self, name).strip()
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            max_slug_length = self._meta.get_field('slug').max_length
            self.slug = slugify(self.name)[:max_slug_length]
        super().save(*args, **kwargs)


class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(unique=True, blank=True, verbose_name='Слаг')

    class Meta:
        verbose_name = 'объект «Категория»'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('events:category_events', kwargs={"cat_slug": self.slug})
    
    def save(self, *args, **kwargs):
        if not self.slug:
            max_slug_length = self._meta.get_field('slug').max_length
            self.slug = slugify(self.name)[:max_slug_length]
        super().save(*args, **kwargs)
