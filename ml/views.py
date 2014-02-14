from django.shortcuts import render
from django.views import generic

class UserListView(generic.TemplateView):
    template_name = 'about.html'
