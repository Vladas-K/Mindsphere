from typing import Any
from django.core.paginator import Paginator
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from datetime import datetime
from .models import Event, Category
from django.views.generic.base import TemplateView
from django.views.generic import ListView
from django.views.generic.detail import DetailView

pub_date = datetime.now()


def category_events(request, slug):
    category = get_object_or_404(Category, slug=slug)
    event_list = Event.objects.filter(category=category).order_by('-pub_date')
    paginator = Paginator(event_list, 2)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    data = {'category': category,
            'page_obj': page_obj,}
    template = 'events/category_events.html'
    return render(request, template, data)

def event_detail_id(request, event_id):
    template = 'events/event_detail_id.html'
    data = {'event_id': event_id, 'pub_date': pub_date}
    return render(request, template, data)

def event_detail(request, slug):
    template = 'events/event_detail.html'
    data = {'slug': slug, 'pub_date': pub_date}
    return render(request, template, data)

def index(request):
    event_list = Event.objects.all().order_by('-pub_date')
    paginator = Paginator(event_list, 2)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'events/index.html'
    title = 'Dievent'
    pub_date = datetime.now()
    data = {'title': title, 
            'pub_date': pub_date, 
            'page_obj': page_obj,}
    return render(request, template, data)


class HomePageView(TemplateView):
    event_list = Event.objects.all().order_by('-pub_date')
    template = 'events/index.html'
    title = 'Dievent'
    pub_date = datetime.now()
    template_name = 'events/index.html'
    paginator = Paginator(event_list, 2)
    # page_number = request.GET.get('page')
    # page_obj = paginator.get_page(page_number)
    def get_context_data(self, **kwargs):
        page_number = self.request.GET.get('page')
        page_obj = self.paginator.get_page(page_number)
        context = super().get_context_data(**kwargs)
        context['event_list'] = Event.objects.all().order_by('-pub_date')
        context['pub_date'] = pub_date
        context['title'] = self.title
        context['page_obj'] = page_obj
        return context