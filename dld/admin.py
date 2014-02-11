from django.contrib import admin
from dld.models import Language


class LanguageAdmin(admin.ModelAdmin):

    search_fields = ['name']


admin.site.register(Language, LanguageAdmin)
