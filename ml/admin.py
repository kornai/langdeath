from django.contrib import admin

from ml.models import Publication, UserProfile, Authorship


class AuthorInline(admin.StackedInline):
    model = Authorship
    extra = 3


class PublicationAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['title', 'year']}),
    ]
    inlines = [AuthorInline]


admin.site.register(UserProfile)
admin.site.register(Publication, PublicationAdmin)
admin.site.register(Authorship)
