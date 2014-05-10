from django.db import models
from django.utils import timezone


class Language(models.Model):
    name = models.CharField(max_length=100)
    native_name = models.CharField(max_length=100)
    sil = models.CharField(max_length=10, unique=True)
    last_updated = models.DateTimeField('last updated', default=timezone.now())
    iso_scope = models.CharField(max_length=20, blank=True)
    iso_type = models.CharField(max_length=100, blank=True)
    champion = models.ForeignKey('Language', blank=True, null=True,
                                 related_name='sublang')
    eth_status = models.CharField(max_length=100, blank=True)
    eth_population = models.IntegerField(blank=True, null=True)
    cru_docs = models.IntegerField(blank=True, null=True)
    cru_words = models.IntegerField(blank=True, null=True)
    cru_characters = models.IntegerField(blank=True, null=True)
    cru_floss_splchk = models.BooleanField(default=False)
    cru_watchtower = models.BooleanField(default=False)
    cru_udhr = models.BooleanField(default=False)
    in_omniglot = models.BooleanField(default=False)

    # many to many fields
    code = models.ManyToManyField('Code', related_name='codes')
    alt_name = models.ManyToManyField('AlternativeName',
                                      related_name='lang')
    country = models.ManyToManyField('Country', related_name='lang')
    speaker = models.ManyToManyField('Speaker', related_name='lang')

    def __unicode__(self):
        return u"{0} ({1})".format(self.name, self.sil)


class Code(models.Model):
    code_name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)


class AlternativeName(models.Model):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class Speaker(models.Model):
    l_type = models.CharField(max_length=2,
                              choices=[("L1", "L1"), ("L2", "L2")])
    source = models.CharField(max_length=100)


class Country(models.Model):
    """iso3611"""
    iso = models.CharField(max_length=2)
    iso3 = models.CharField(max_length=3)
    name = models.CharField(max_length=100, unique=True)
    capital = models.CharField(max_length=100, blank=True)
    area = models.FloatField(default=0, blank=True, null=True)
    population = models.IntegerField(blank=True, null=True)
    continent = models.CharField(max_length=100, null=True)
    tld = models.CharField(max_length=10, null=True)
    native_name = models.CharField(max_length=100, blank=True, null=True)

    def __unicode__(self):
        return self.name


class CountryName(models.Model):
    """Alternative country names"""
    country = models.ForeignKey("Country")
    name = models.CharField(max_length=100)
