from django.conf.urls import patterns, url

from dld import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^home$', views.index, name='home'),
    url(r'^news$', views.NewsView.as_view(), name='news'),
    url(r'^list$', views.LanguageListView.as_view(), name='list'),
    url(r'^search$', views.search, name='search'),
    url(r'^(?P<pk>\w+)$', views.LanguageDetailsView.as_view(), name='details'),
)
