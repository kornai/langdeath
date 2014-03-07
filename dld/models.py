from django.db import models
from django.utils import timezone
from jsonfield import JSONField


class Language(models.Model):

    english_name = models.CharField(max_length=100)
    sil = models.CharField(max_length=10, primary_key=True)
    local_name = models.CharField(max_length=100, blank=True)
    last_updated = models.DateTimeField('last updated', default=timezone.now())
    l1_speakers = JSONField()
    other_codes = JSONField()

    def __unicode__(self):
        return u"{0} ({1})".format(self.english_name, self.sil)
