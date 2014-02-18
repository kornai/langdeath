from django.db import models

from django.contrib.auth.models import User
from django.db.models.signals import post_save
 

class Publication(models.Model):
    title = models.TextField(max_length=200)
    year = models.IntegerField()

    def __unicode__(self):
        return u'{0}: {1} ({2})'.format(self.short_authors_list(),
                                        self.title, self.year)

    def short_authors_list(self):
        s = list()
        for authorship in self.authorship_set.all():
            author = authorship.author.user
            if not author.first_name or not author.last_name:
                s.append(author.username)
            else:
                s.append(u'{0}. {1}'.format(author.first_name[0], author.last_name))
        return ', '.join(s)


class UserProfile(models.Model):  
    user = models.OneToOneField(User)
    group_member = models.BooleanField(default=False)
    leader = models.BooleanField(default=False)
    image = models.ImageField(upload_to='profile', blank=True)

    def __unicode__(self):  
        name = ''
        if not self.user.last_name or not self.user.first_name:
            name = self.user.username
        else:
            name = self.user.first_name + ' ' + self.user.last_name
        return name
 

class Authorship(models.Model):
    author = models.ForeignKey(UserProfile)
    publication = models.ForeignKey(Publication)


def create_user_profile(sender, instance, created, **kwargs):  
    if created:  
       profile, created = UserProfile.objects.get_or_create(user=instance)  
 
post_save.connect(create_user_profile, sender=User)
 
User.profile = property(lambda u: u.get_profile() )

