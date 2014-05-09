from django.forms import ModelForm, CharField

from dld.models import Language


class LanguageSearchForm(ModelForm):
    name = CharField(required=False, label='English name')
    native_name = CharField(required=False, label='Alternative name')
    sil = CharField(required=False, label='SIL code')

    class Meta:
        model = Language
        fields = ['name', 'native_name', 'sil']

    def get_languages(self):
        return Language.objects.filter(name__contains=self.cleaned_data['name'].strip(),
                native_name__contains=self.cleaned_data['native_name'].strip(),
                sil__contains=self.cleaned_data['sil'].strip())
