from django.contrib import admin
from .models import RulesetVersion, Campaign, Membership, Asset

@admin.register(RulesetVersion)
class RulesetAdmin(admin.ModelAdmin):
    def has_change_permission(self, request, obj=None):
        return obj is None

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register([Campaign, Membership, Asset])
