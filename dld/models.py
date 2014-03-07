from django.db import models
from jsonfield import JSONField


class Language(models.Model):

    name = models.CharField(max_length=100)
    local_name = models.CharField(max_length=100)
    sil = models.CharField(max_length=10, primary_key=True)
    last_updated = models.DateTimeField('last updated')
    l1_speakers = JSONField()
    other_codes = JSONField()
