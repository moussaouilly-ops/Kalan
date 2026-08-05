from rest_framework import serializers

from .models import AffiliateClick, AffiliateCommission, AffiliateLink, AffiliateProfile


class AffiliateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffiliateProfile
        fields = ["id", "affiliate_code", "commission_percent", "total_earned", "is_active", "created_at"]
        read_only_fields = ["affiliate_code", "total_earned", "created_at"]


class AffiliateLinkSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)
    conversion_rate = serializers.SerializerMethodField()

    class Meta:
        model = AffiliateLink
        fields = [
            "id", "course", "course_title", "tracking_code",
            "total_clicks", "total_conversions", "conversion_rate", "created_at",
        ]
        read_only_fields = ["tracking_code", "total_clicks", "total_conversions", "created_at"]

    def get_conversion_rate(self, obj):
        if not obj.total_clicks:
            return 0
        return round((obj.total_conversions / obj.total_clicks) * 100, 1)

    def create(self, validated_data):
        import uuid
        validated_data["tracking_code"] = uuid.uuid4().hex[:10]
        return super().create(validated_data)


class AffiliateClickSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffiliateClick
        fields = ["id", "link", "clicked_at"]
        read_only_fields = ["clicked_at"]


class AffiliateCommissionSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="link.course.title", read_only=True)

    class Meta:
        model = AffiliateCommission
        fields = ["id", "link", "course_title", "amount", "status", "created_at", "paid_at"]
        read_only_fields = fields
