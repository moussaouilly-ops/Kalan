from django.contrib import admin

from .models import AffiliateClick, AffiliateCommission, AffiliateLink, AffiliateProfile


@admin.register(AffiliateProfile)
class AffiliateProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "affiliate_code", "commission_percent", "total_earned", "is_active"]


@admin.register(AffiliateLink)
class AffiliateLinkAdmin(admin.ModelAdmin):
    list_display = ["affiliate", "course", "tracking_code", "total_clicks", "total_conversions"]


admin.site.register(AffiliateClick)
admin.site.register(AffiliateCommission)
