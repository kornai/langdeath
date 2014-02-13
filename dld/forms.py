from django.forms import ModelForm, CharField

from dld.models import Language

class LanguageSearchForm(ModelForm):
    name = CharField(required=False)
    name2 = CharField(required=False)
    sil = CharField(required=False)

    class Meta:
        model = Language
        fields = ['name', 'name2', 'sil']
        labels = {
            'name': 'English name',
            'name2': 'Alternative name',
            'sil': 'SIL code',
        }

    def get_languages(self):
        return Language.objects.filter(name__contains=self.cleaned_data['name'],
                                      name2__contains=self.cleaned_data['name2'],
                                      sil__contains=self.cleaned_data['sil'])

