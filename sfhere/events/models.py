from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model() 


class Event(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(max_length=400)
    pub_date = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(
    'Category', 
    blank=True, 
    null=True,
    on_delete=models.SET_NULL,
    related_name='cats'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='events/',
        blank=True
    )  

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("events:event_detail_id", kwargs={"event_id": self.pk})
    
    

class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name