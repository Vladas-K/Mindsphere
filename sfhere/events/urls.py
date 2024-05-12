from django.urls import path
from django.views.generic import TemplateView
from events import views
from events.views import (CategoryListView, EventCreateView, EventDetailView,
                          EventListView, EventUpdateView)

app_name = 'events'

urlpatterns = [
    path('', EventListView.as_view(), name='index'),
    path('category/<slug:cat_slug>/', CategoryListView.as_view(), name='category_events'),
    path('events/<slug:slug>/', EventDetailView.as_view(), name='event_detail'),
    path("about/", TemplateView.as_view(template_name='events/about.html')),
    path('create/', EventCreateView.as_view(), name='event_create'),
    path('events/<slug:slug>/edit/', EventUpdateView.as_view(), name='event_edit'),
]