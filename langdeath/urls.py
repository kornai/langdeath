from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^lang/', include('dld.urls')),
    url(r'^ml/', include('ml.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
