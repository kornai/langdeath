"""langdeath2 URL Configuration
"""
from django.conf.urls import patterns, url
from django.contrib import admin
from dld import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.index, name='index'),
    url(r'^news$', views.NewsView.as_view(), name='news'),
    url(r'^list$', views.LanguageListView.as_view(), name='list'),
    url(r'^search$', views.search, name='search'),
    url(r'^(?P<pk>\w+)$', views.LanguageDetailsView.as_view(), name='details'),
]

