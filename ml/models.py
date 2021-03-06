from django.db import models

from django.contrib.auth.models import User
from django.db.models.signals import post_save


class Resource(models.Model):
    name = models.TextField(max_length=200)
    description = models.TextField(max_length=2000)
    url = models.TextField(max_length=200, blank=True)

    def __unicode__(self):
        return self.name


class Publication(models.Model):
    title = models.TextField(max_length=200)
    year = models.IntegerField()

    def __unicode__(self):
        return u'{0}: {1} ({2})'.format(self.short_authors_list(),
                                        self.title, self.year)

    def short_authors_list(self):
        s = list()
        for authorship in self.publicationauthorship_set.all():
            author = authorship.author.user
            if not author.first_name or not author.last_name:
                s.append(author.username)
            else:
                s.append(u'{0}. {1}'.format(author.first_name[0],
                                            author.last_name))
        return ', '.join(s)


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    membership_choices = (('M', 'Member'),
                          ('X', 'Ex-member'),
                          ('N', 'Non-member'),
                          ('L', 'Leader'))
    membership = models.CharField(max_length=1,
                                  choices=membership_choices,
                                  default='N')
    image = models.ImageField(upload_to='profile', blank=True)

    def __unicode__(self):
        name = ''
        if not self.user.last_name or not self.user.first_name:
            name = self.user.username
        else:
            name = self.user.first_name + ' ' + self.user.last_name
        return name


class PublicationAuthorship(models.Model):
    author = models.ForeignKey(UserProfile)
    publication = models.ForeignKey(Publication)


class ResourceAuthorship(models.Model):
    author = models.ForeignKey(UserProfile)
    resource = models.ForeignKey(Resource)


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile, created = UserProfile.objects.get_or_create(user=instance)

post_save.connect(create_user_profile, sender=User)
User.profile = property(lambda u: u.get_profile())
