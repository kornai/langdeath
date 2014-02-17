from django.conf.urls import patterns, url

from ml import views

urlpatterns = patterns('',
    url(r'^$', views.UserListView.as_view(), name='index'),
    url(r'^home$', views.UserListView.as_view(), name='index'),
    #url(r'^home$', views.index, name='home'),
    #url(r'^news$', views.NewsView.as_view(), name='news'),
    #url(r'^list$', views.LanguageListView.as_view(), name='list'),
    #url(r'^about$', views.AboutUsView.as_view(), name='about'),
    #url(r'^search$', views.search, name='search'),
    #url(r'^(?P<pk>\w+)$', views.LanguageDetailsView.as_view(), name='details'),
)
