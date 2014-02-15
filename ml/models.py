from django.db import models

from django.contrib.auth.models import User
from django.db.models.signals import post_save


class UserProfile(models.Model):
    user = models.OneToOneField(User, blank=True)

    def __unicode__(self):
        return ' '.join([self.user.first_name,
                         self.user.last_name])


class Publication(models.Model):
    year = models.IntegerField(blank=True)
    title = models.CharField(max_length=200)

    def __unicode__(self):
        return self.title + ' (' + str(self.year) + ')'


class Authorship(models.Model):
    author = models.ForeignKey(UserProfile)
    publication = models.ForeignKey(Publication)

    def __unicode__(self):
        return 'authorship: {0} {1}'.format(self.author, self.publication)


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile, created = UserProfile.objects.get_or_create(user=instance)

post_save.connect(create_user_profile, sender=User)

User.profile = property(lambda u: u.get_profile())
