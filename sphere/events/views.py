from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .forms import EventForm
from .models import Category, Event

pub_date = datetime.now()


class EventListView(ListView):
    model = Event
    paginate_by = 5
    template_name = 'events/index.html'

    def get_queryset(self):
        return Event.objects.order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Dievent'
        return context


class CategoryListView(ListView):
    model = Event
    paginate_by = 5
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


class EventCreateView(LoginRequiredMixin, CreateView):
    template_name = 'events/event_create.html'
    form_class = EventForm

    def get_success_url(self):
        return reverse('events:index')


class EventUpdateView(LoginRequiredMixin, UpdateView):
    model = Event
    template_name = 'events/event_create.html'
    form_class = EventForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context

    def get_success_url(self):
        return reverse('events:index')


class EventDeleteView(LoginRequiredMixin, DeleteView):
    model = Event
    template_name = 'events/event_confirm_delete.html'
    success_url = reverse_lazy('events:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_delete'] = True
        return context
