from django.conf.urls import patterns, url

from ml import views

urlpatterns = patterns(
    '',
    url(r'^$', views.IndexView.as_view(), name='ml_home'),
    url(r'^publ$', views.PublicationListView.as_view(), name='publ'),
    url(r'^publ/(?P<pk>\d+)$', views.PublicationDetailView.as_view(), name='publ'),
    url(r'^res$', views.ResourcesView.as_view(), name='res'),
    url(r'^about$', views.GroupView.as_view(), name='about'),
    url(r'^user/(?P<username>\w+)$', views.get_profile, name='profile'),
)
