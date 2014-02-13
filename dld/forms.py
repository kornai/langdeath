from django.forms import ModelForm

from dld.models import Language

class LanguageSearchForm(ModelForm):
    class Meta:
        model = Language
        fields = ['name', 'name2', 'sil']

    def get_languages(self):
        if self.cleaned_data['name']:
            return Language.objects.filter(name__startswith=self.cleaned_data['name'])

