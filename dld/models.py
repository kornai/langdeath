from django.db import models
from django.utils import timezone


class Language(models.Model):
    name = models.CharField(max_length=100)
    native_name = models.CharField(max_length=100)
    sil = models.CharField(max_length=10, primary_key=True)
    last_updated = models.DateTimeField('last updated', default=timezone.now())
    iso_scope = models.CharField(max_length=20, blank=True)
    iso_type = models.CharField(max_length=100, blank=True)
    eth_status = models.CharField(max_length=100, blank=True)
    eth_population = models.IntegerField(blank=True, null=True)
    cru_docs = models.IntegerField(blank=True, null=True)
    cru_words = models.IntegerField(blank=True, null=True)
    cru_characters = models.IntegerField(blank=True, null=True)
    cru_floss_splchk = models.BooleanField(default=False)
    cru_watchtower = models.BooleanField(default=False)
    cru_udhr = models.BooleanField(default=False)

    def __unicode__(self):
        return u"{0} ({1})".format(self.name, self.sil)


class Code(models.Model):
    language = models.ForeignKey("Language")
    code_name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)


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
