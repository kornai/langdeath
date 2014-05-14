from django.db import models
from django.utils import timezone

def normalize_alt_name(name):
    remove_punct = name.replace(",", "").replace("(", "")
    remove_punct = remove_punct.replace(")", "")
    return " ".join(set(remove_punct.lower().split()))


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

    la_primary_texts_online = models.IntegerField(blank=True, null=True)
    la_primary_texts_all = models.IntegerField(blank=True, null=True)
    la_lang_descr_online = models.IntegerField(blank=True, null=True)
    la_lang_descr_all = models.IntegerField(blank=True, null=True)
    la_lex_res_online = models.IntegerField(blank=True, null=True)
    la_lex_res_all = models.IntegerField(blank=True, null=True)
    la_res_in_online = models.IntegerField(blank=True, null=True)
    la_res_in_all = models.IntegerField(blank=True, null=True)
    la_res_about_online = models.IntegerField(blank=True, null=True)
    la_res_about_all = models.IntegerField(blank=True, null=True)
    la_oth_res_in_online = models.IntegerField(blank=True, null=True)
    la_oth_res_in_all = models.IntegerField(blank=True, null=True)
    la_oth_res_about_online = models.IntegerField(blank=True, null=True)
    la_oth_res_about_all = models.IntegerField(blank=True, null=True)

    # many to many fields
    code = models.ManyToManyField('Code', related_name='codes')
    alt_name = models.ManyToManyField('AlternativeName',
                                      through='LanguageAltName',
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

    def save(self, force_insert=False, force_update=False):
        self.name = normalize_alt_name(self.name)
        super(AlternativeName, self).save(force_insert, force_update)


class LanguageAltName(models.Model):
    lang = models.ForeignKey(Language)
    name = models.ForeignKey(AlternativeName)

    class Meta:
        unique_together = (("lang", "name"), )


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
