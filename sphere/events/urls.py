from django.urls import path
from django.views.generic import TemplateView

from events.views import (CategoryListView, EventCreateView, EventDeleteView,
                          EventDetailView, EventListView, EventUpdateView)

app_name = 'events'

urlpatterns = [
    path('', EventListView.as_view(), name='index'),
    path('category/<slug:cat_slug>/', CategoryListView.as_view(), name='category_events'),
    path('events/<slug:slug>/', EventDetailView.as_view(), name='event_detail'),
    path('about/', TemplateView.as_view(template_name='events/about.html'), name='about'),
    path('create/', EventCreateView.as_view(), name='event_create'),
    path('events/<slug:slug>/edit/', EventUpdateView.as_view(), name='event_edit'),
    path('events/<slug:slug>/delete/', EventDeleteView.as_view(), name='event_delete'),
]
