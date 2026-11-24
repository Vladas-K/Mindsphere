from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .forms import EventForm
from .models import Category, Event
from .catalog import prepare_program


class EventListView(ListView):
    model = Event
    template_name = 'events/index.html'

    def get_queryset(self):
        return Event.objects.filter(is_published=True).select_related('category').defer('description')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Авторские программы'
        events = list(context['event_list'])
        context['programs'] = [
            prepare_program(event, number, len(events))
            for number, event in enumerate(events, 1)
        ]
        return context


class CategoryListView(EventListView):

    def get_category(self):
        if not hasattr(self, 'category'):
            self.category = get_object_or_404(Category, slug=self.kwargs['cat_slug'])
        return self.category

    def get_queryset(self):
        category = self.get_category()
        return super().get_queryset().filter(category=category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.get_category()
        context['title'] = self.category.name
        return context


class EventDetailView(LoginRequiredMixin, DetailView):
    model = Event

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['program'] = prepare_program(self.object, self.object.sort_order or 1, Event.objects.filter(is_published=True).count())
        return context


class EventMixin(LoginRequiredMixin):
    model = Event
    template_name = 'events/event_create.html'
    form_class = EventForm

    def get_success_url(self):
        return reverse_lazy('events:index')


class EventCreateView(EventMixin, CreateView):
    pass


class EventUpdateView(EventMixin, UpdateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context


class EventDeleteView(LoginRequiredMixin, DeleteView):
    model = Event
    template_name = 'events/event_confirm_delete.html'
    success_url = reverse_lazy('events:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_delete'] = True
        return context
