from django.contrib import admin

from ml import models


class ResourceAuthorshipInline(admin.StackedInline):
    model = models.ResourceAuthorship
    extra = 3


class ResourceAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['name', 'description', 'url']}),
    ]
    inlines = [ResourceAuthorshipInline]


class PublicationAuthorshipInline(admin.StackedInline):
    model = models.PublicationAuthorship
    extra = 3


class PublicationAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['title', 'year']}),
    ]
    inlines = [PublicationAuthorshipInline]


admin.site.register(models.Resource, ResourceAdmin)
admin.site.register(models.ResourceAuthorship)
admin.site.register(models.Publication, PublicationAdmin)
admin.site.register(models.PublicationAuthorship)
admin.site.register(models.UserProfile)
