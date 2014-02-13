from django.forms import ModelForm, CharField

from dld.models import Language

class LanguageSearchForm(ModelForm):
    name = CharField(required=False, label='English name')
    name2 = CharField(required=False, label='Alternative name')
    sil = CharField(required=False, label='SIL code')

    class Meta:
        model = Language
        fields = ['name', 'name2', 'sil']

    def get_languages(self):
        return Language.objects.filter(name__contains=self.cleaned_data['name'],
                                      name2__contains=self.cleaned_data['name2'],
                                      sil__contains=self.cleaned_data['sil'])

