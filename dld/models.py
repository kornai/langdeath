from django.db import models


class Language(models.Model):

    name = models.CharField(max_length=100)
    name2= models.CharField(max_length=100)
    iso639_3 = models.CharField(max_length=10)
    last_updated = models.DateTimeField('last updated')
    #character_entropy = models.CharField(max_length=10)


