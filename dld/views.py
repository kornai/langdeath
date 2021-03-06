from django.shortcuts import render

from django.views import generic

from dld.models import Language
from dld.forms import LanguageSearchForm


class LanguageListView(generic.ListView):
    template_name = 'dld_index.html'
    context_object_name = 'languages'

    def get_queryset(self):
        return Language.objects.order_by('-last_updated')


class NewsView(generic.ListView):
    template_name = 'dld_news.html'
    context_object_name = 'latest_updated_langs'

    def get_queryset(self):
        return Language.objects.order_by('-last_updated')


class LanguageDetailsView(generic.DetailView):
    template_name = 'lang_detail.html'
    model = Language


def index(request):
    context = {'languages': Language.objects.order_by('-last_updated')}
    return render(request, 'dld_index.html', context)


def search(request):
    if request.method == 'POST':
        form = LanguageSearchForm(request.POST)
        if form.is_valid():
            langs = form.get_languages()
            context = {'languages': langs}
            return render(request, 'lang_results.html', context)
    else:
        form = LanguageSearchForm()
    return render(request, 'lang_search.html', {'form': form})
