from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.index, name='index'),
    path('category/<slug:slug>/', views.category_events, name = 'category_events'),
    path('events/<int:event_id>/', views.event_detail_id, name='event_detail_id'),
    path('events/<slug:slug>/', views.event_detail, name='event_detail'),
]