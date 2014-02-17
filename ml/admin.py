from django.contrib import admin

from ml import models


class AuthorshipInline(admin.StackedInline):
    model = models.Authorship
    extra = 3

class PublicationAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['title', 'year']}),
    ]
    inlines = [AuthorshipInline]

admin.site.register(models.Publication, PublicationAdmin)
admin.site.register(models.UserProfile)
admin.site.register(models.Authorship)
