#from django.shortcuts import render
from django.views import generic
import logging

logger = logging.getLogger('langdeath')


class UserListView(generic.TemplateView):
    template_name = 'ml_index.html'
    logger.debug('UserListView created')
