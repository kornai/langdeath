from django.conf.urls import patterns, url

from dld import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^news$', views.NewsView.as_view(), name='news'),
    url(r'^list$', views.LanguageListView.as_view(), name='list'),
    url(r'^about$', views.AboutUsView.as_view(), name='about'),
    url(r'^search$', views.search, name='search'),
    #url(r'^results$', views.SearchResultsView.as_view(), name='results'),
    url(r'^(?P<pk>\w+)$', views.LanguageDetailsView.as_view(), name='details'),
)
