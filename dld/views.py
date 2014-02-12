from django.shortcuts import render, get_object_or_404

from django.http import HttpResponse, Http404
from django.views import generic

from dld.models import Language


class LanguageListView(generic.ListView):
    template_name = 'index.html'
    context_object_name = 'languages'
    
    def get_queryset(self):
        return Language.objects.order_by('-last_updated')


class NewsView(generic.ListView):
    template_name = 'news.html'
    context_object_name = 'latest_updated_langs'
    
    def get_queryset(self):
        return Language.objects.order_by('-last_updated')


class LanguageDetailsView(generic.DetailView):
    template_name = 'detail.html'
    model = Language
    

class AboutUsView(generic.TemplateView):
    template_name = 'about.html'


def index(request):
    context = {'languages': Language.objects.order_by('-last_updated')}
    return render(request, 'index.html', context)

