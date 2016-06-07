from django.db import models
from django.utils import timezone


def normalize_alt_name(name):
    remove_punct = name.replace(",", "").replace("(", "")
    remove_punct = remove_punct.replace(")", "")
    return " ".join(sorted(remove_punct.lower().split()))


class Language(models.Model):
    name = models.CharField(max_length=100)
    native_name = models.CharField(max_length=100)
    sil = models.CharField(max_length=20, unique=True)
    last_updated = models.DateTimeField('last updated', default=timezone.now())
    iso_scope = models.CharField(max_length=20, blank=True)
    iso_type = models.CharField(max_length=100, blank=True)
    eth_population = models.IntegerField(blank=True, null=True)
    
    find_bible_all_versions = models.IntegerField(blank=True, null=True)
    cru_docs = models.IntegerField(blank=True, null=True)
    cru_words = models.IntegerField(blank=True, null=True)
    cru_characters = models.IntegerField(blank=True, null=True)
    cru_floss_splchk = models.BooleanField(default=False)
    cru_watchtower = models.BooleanField(default=False)
    cru_udhr = models.BooleanField(default=False)
    in_omniglot = models.BooleanField(default=False)
    uriel_feats = models.IntegerField(blank=True, null=True)
    on_bible_org = models.BooleanField(default=False)
    in_leipzig_corpora = models.BooleanField(default=False)
    in_siren_project = models.BooleanField(default=False)
    treetagger = models.BooleanField(default=False)

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

    mac_input = models.BooleanField(default=False)
    mac_input_partial = models.BooleanField(default=False)
    microsoft_pack = models.BooleanField(default=False)
    win10_input_method = models.BooleanField(default=False)
    ubuntu_pack = models.BooleanField(default=False)
    ubuntu_input = models.BooleanField(default=False)
    office13_if_pack = models.BooleanField(default=False)
    office13_lp = models.BooleanField(default=False)
    hunspell_status = models.CharField(max_length=100, blank=True)
    hunspell_coverage = models.FloatField(blank=True, null=True)

    firefox_lpack = models.BooleanField(default=False)
    firefox_dict = models.BooleanField(default=False)

    wals_samples_100 = models.BooleanField(default=False)
    wals_samples_200 = models.BooleanField(default=False)

    indi_blogs = models.IntegerField(blank=True, null=True)
    indi_posts = models.IntegerField(blank=True, null=True)
    indi_words = models.IntegerField(blank=True, null=True)
    indi_users = models.IntegerField(blank=True, null=True)
    indi_tweets = models.IntegerField(blank=True, null=True)

    wp_articles = models.IntegerField(blank=True, null=True)
    wp_total = models.IntegerField(blank=True, null=True)
    wp_edits = models.IntegerField(blank=True, null=True)
    wp_admins = models.IntegerField(blank=True, null=True)
    wp_users = models.IntegerField(blank=True, null=True)
    wp_active_users = models.IntegerField(blank=True, null=True)
    wp_images = models.IntegerField(blank=True, null=True)
    wp_depth = models.IntegerField(blank=True, null=True)
    wp_inc = models.BooleanField(default=False)
    wp_real_articles = models.FloatField(blank=True, null=True)
    wp_adjusted_size = models.FloatField(blank=True, null=True)

    ## many to one fields
    champion = models.ForeignKey('self', blank=True, null=True,
                                 related_name='sublang')
    macrolang = models.ForeignKey('self', blank=True, null=True,
                                  related_name='sublang2')

    ## many to many fields
    code = models.ManyToManyField('Code', related_name='codes')
    alt_name = models.ManyToManyField('AlternativeName',
                                      through='LanguageAltName',
                                      related_name='lang')
    country = models.ManyToManyField('Country', related_name='lang')
    speakers = models.ManyToManyField('Speaker', related_name='lang')
    endangered_levels = models.ManyToManyField('EndangeredLevel',
                                               related_name='Language')
    locations = models.ManyToManyField('Coordinates', related_name='Language')

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
    src = models.CharField(max_length=1000)
    num = models.IntegerField(blank=True, null=True)


class EndangeredLevel(models.Model):
    src = models.CharField(max_length=1000)
    level = models.CharField(max_length=100)
    confidence = models.FloatField(blank=True, null=True)


class Coordinates(models.Model):
    src = models.CharField(max_length=1000)
    longitude = models.FloatField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)


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
