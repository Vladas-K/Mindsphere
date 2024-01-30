from django.urls import path
from events import views
from django.views.generic import TemplateView
from events.views import EventListView, CategoryListView, EventDetailView

app_name = 'events'

urlpatterns = [
    # path('', HomePageView.as_view(), name='index'),
    # # path('', views.index, name='index'),
    path('', EventListView.as_view(), name='index'),
    path('category/<slug:cat_slug>/', CategoryListView.as_view(), name='category_events'),
    path('events/<slug:slug>/', EventDetailView.as_view(), name='event_detail'),
    # path('category/<slug:slug>/', views.category_events, name = 'category_events'),
    # path('events/<int:event_id>/', views.event_detail_id, name='event_detail_id'),
    # path('events/<slug:slug>/', views.event_detail, name='event_detail'),
    path("about/", TemplateView.as_view(template_name='events/about.html'))
]