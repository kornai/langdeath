from django.contrib import admin

from ml import models


class PublicationAuthorshipInline(admin.StackedInline):
    model = models.PublicationAuthorship
    extra = 3

class PublicationAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['title', 'year']}),
    ]
    inlines = [PublicationAuthorshipInline]

admin.site.register(models.Publication, PublicationAdmin)
admin.site.register(models.UserProfile)
admin.site.register(models.PublicationAuthorship)
