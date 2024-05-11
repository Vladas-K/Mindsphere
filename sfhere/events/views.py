from typing import Any
from django.core.paginator import Paginator
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.shortcuts import redirect ,render, get_object_or_404
from datetime import datetime
from .models import Event, Category
from django.views.generic.base import TemplateView
from django.views.generic import ListView
from django.views.generic.detail import DetailView

from .forms import EventForm

pub_date = datetime.now()


class EventListView(ListView):
    model = Event
    paginate_by = 2
    template_name = 'events/index.html'

    def get_queryset(self):
        return Event.objects.order_by('-pub_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Dievent'
        return context
    
    
class CategoryListView(ListView):
    model = Event
    paginate_by = 2
    template_name = 'events/category_events.html'

    def get_category(self):
        return get_object_or_404(Category, slug=self.kwargs['cat_slug'])

    def get_queryset(self):
        category = self.get_category()
        queryset = Event.objects.filter(category=category).order_by('-pub_date')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_category()
        context['category'] = category
        return context  
        
 
class EventDetailView(DetailView):
    template_name = 'events/event_detail_id.html'
    model = Event

def event_create(request):

    if request.method == 'POST':
    
        form = EventForm(request.POST, request.FILES)

        if form.is_valid():
            post = form.save(False)
            post.author = request.user
            post.save()
            return redirect('events:index')
    
    else:
        form = EventForm()

    return render(request, 'events/event_create.html', {'form': form, })

