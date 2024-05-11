from django.urls import path
from events import views
from django.views.generic import TemplateView
from events.views import EventListView, CategoryListView, EventDetailView

app_name = 'events'

urlpatterns = [
    path('', EventListView.as_view(), name='index'),
    path('category/<slug:cat_slug>/', CategoryListView.as_view(), name='category_events'),
    path('events/<slug:slug>/', EventDetailView.as_view(), name='event_detail'),
    path("about/", TemplateView.as_view(template_name='events/about.html')),
    path('create/', views.event_create, name='event_create'),
]