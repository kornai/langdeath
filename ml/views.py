from django.shortcuts import render
from django.views import generic

from ml.models import UserProfile, Publication


class GroupView(generic.ListView):
    template_name = 'group.html'
    context_object_name = 'users'

    def get_queryset(self):
        try:
            users = [UserProfile.objects.get(leader=True)]
        except UserProfile.DoesNotExist:
            users = []
        users.extend(list(UserProfile.objects.filter(
            group_member=True, leader=False)))
        return users


def get_profile(request, username):
    context = {'user': UserProfile.objects.get(user__username=username)}
    return render(request, 'user.html', context)


class PublicationListView(generic.ListView):
    template_name = 'publ_list.html'
    context_object_name = 'publications'

    def get_queryset(self):
        return Publication.objects.order_by('-year')


class ResourcesView(generic.ListView):
    template_name = 'res_list.html'
    context_object_name = 'resources'


class IndexView(generic.TemplateView):
    template_name = 'ml_home.html'
