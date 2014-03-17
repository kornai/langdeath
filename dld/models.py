from django.db import models
from django.utils import timezone
from jsonfield import JSONField


class Language(models.Model):
    name = models.CharField(max_length=100)
    native_name = models.CharField(max_length=100)
    sil = models.CharField(max_length=10, primary_key=True)
    last_updated = models.DateTimeField('last updated', default=timezone.now())
    l1_speakers = JSONField()
    other_codes = JSONField()

    def __unicode__(self):
        return u"{0} ({1})".format(self.english_name, self.sil)


class AlternativeName(models.Model):
    language = models.ForeignKey("Language")
    name = models.CharField(max_length=100)


class Speaker(models.Model):
    language = models.ForeignKey("Language")
    l_type = models.CharField(max_length=2,
                              choices=[("L1", "L1"), ("L2", "L2")])
    source = models.CharField(max_length=100)


class Country(models.Model):
    """iso3611"""
    iso = models.CharField(max_length=2)
    iso3 = models.CharField(max_length=3)
    name = models.CharField(max_length=100)
    capital = models.CharField(max_length=100)
    area = models.FloatField(default=0, blank=True)
    population = models.IntegerField()
    continent = models.CharField(max_length=100)
    tld = models.CharField(max_length=10)
    native_name = models.CharField(max_length=100, blank=True)


class LanguageCountry(models.Model):
    language = models.ForeignKey("Language")
    country = models.ForeignKey("Country")


class CountryName(models.Model):
    """Alternative country names"""
    country = models.ForeignKey("Country")
    name = models.CharField(max_length=100)
