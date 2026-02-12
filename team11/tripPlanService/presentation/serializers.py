from rest_framework import serializers
from data.models import (
    Trip, TripDay, TripItem, ItemDependency,
    ShareLink, Vote, TripReview, UserMedia
)


class TripItemSerializer(serializers.ModelSerializer):
    """Serializer for TripItem model"""

    class Meta:
        model = TripItem
        fields = [
            'item_id', 'item_type', 'place_ref_id', 'title', 'category',
            'address_summary', 'lat', 'lng', 'wiki_summary', 'wiki_link',
            'main_image_url', 'start_time', 'end_time', 'duration_minutes',
            'sort_order', 'is_locked', 'price_tier', 'estimated_cost',
            'transport_mode_to_next', 'travel_time_to_next', 'travel_distance_to_next'
        ]
        read_only_fields = ['item_id']

    def validate(self, data):
        """Validate time fields"""
        if 'start_time' in data and 'end_time' in data:
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError(
                    "End time must be after start time"
                )

        if 'duration_minutes' in data and data['duration_minutes'] < 60:
            raise serializers.ValidationError(
                "Duration must be at least 60 minutes"
            )

        return data


class ItemDependencySerializer(serializers.ModelSerializer):
    """Serializer for ItemDependency model"""

    prerequisite_title = serializers.CharField(
        source='prerequisite_item.title',
        read_only=True
    )

    class Meta:
        model = ItemDependency
        fields = [
            'dependency_id', 'item', 'prerequisite_item',
            'prerequisite_title', 'dependency_type', 'violation_action'
        ]
        read_only_fields = ['dependency_id']


class VoteSerializer(serializers.ModelSerializer):
    """Serializer for Vote model"""

    class Meta:
        model = Vote
        fields = ['vote_id', 'item', 'guest_session_id',
                  'is_upvote', 'created_at']
        read_only_fields = ['vote_id', 'created_at']


class TripDaySerializer(serializers.ModelSerializer):
    """Serializer for TripDay model"""

    items = TripItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = TripDay
        fields = [
            'day_id', 'day_index', 'specific_date',
            'start_geo_location', 'items', 'items_count'
        ]
        read_only_fields = ['day_id']

    def get_items_count(self, obj):
        """Get number of items in this day"""
        return obj.items.count()


class ShareLinkSerializer(serializers.ModelSerializer):
    """Serializer for ShareLink model"""

    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = ShareLink
        fields = [
            'link_id', 'token', 'expires_at', 'permission',
            'created_at', 'is_expired'
        ]
        read_only_fields = ['link_id', 'token', 'created_at']

    def get_is_expired(self, obj):
        """Check if link is expired"""
        from django.utils import timezone
        return obj.expires_at < timezone.now()


class TripReviewSerializer(serializers.ModelSerializer):
    """Serializer for TripReview model"""

    class Meta:
        model = TripReview
        fields = [
            'review_id', 'trip', 'item', 'rating',
            'comment', 'sent_to_central_service', 'created_at'
        ]
        read_only_fields = ['review_id',
                            'created_at', 'sent_to_central_service']

    def validate_rating(self, value):
        """Validate rating is between 1 and 5"""
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value


class UserMediaSerializer(serializers.ModelSerializer):
    """Serializer for UserMedia model"""

    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UserMedia
        fields = [
            'media_id', 'trip', 'user', 'username',
            'media_url', 'caption', 'media_type', 'uploaded_at'
        ]
        read_only_fields = ['media_id', 'uploaded_at']


class TripListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for trip lists"""

    days_count = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            'trip_id', 'title', 'location', 'province', 'city',
            'start_date', 'end_date', 'duration_days',
            'budget_level', 'travel_style', 'status',
            'days_count', 'created_at'
        ]
        read_only_fields = ['trip_id', 'created_at', 'end_date']

    def get_days_count(self, obj):
        """Get number of days in trip"""
        return obj.days.count() if hasattr(obj, 'days') else 0

    def get_location(self, obj):
        """Get formatted location"""
        return obj.city if obj.city else obj.province


class TripDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single trip view"""

    days = TripDaySerializer(many=True, read_only=True)
    share_links = ShareLinkSerializer(many=True, read_only=True)
    reviews = TripReviewSerializer(many=True, read_only=True)
    media = UserMediaSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Trip
        fields = [
            'trip_id', 'user', 'username', 'copied_from_trip',
            'title', 'province', 'city', 'start_date', 'end_date',
            'duration_days', 'budget_level', 'daily_available_hours',
            'travel_style', 'generation_strategy', 'status',
            'total_estimated_cost', 'reminder_enabled', 'created_at',
            'days', 'share_links', 'reviews', 'media', 'average_rating'
        ]
        read_only_fields = ['trip_id', 'created_at', 'end_date']

    def get_average_rating(self, obj):
        """Calculate average rating"""
        reviews = obj.reviews.all()
        if not reviews:
            return None
        return sum(r.rating for r in reviews) / len(reviews)


class TripCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating trips"""

    class Meta:
        model = Trip
        fields = [
            'title', 'province', 'city', 'start_date', 'duration_days',
            'budget_level', 'daily_available_hours', 'travel_style',
            'generation_strategy', 'status', 'reminder_enabled'
        ]

    def validate_duration_days(self, value):
        """Validate duration is within acceptable range"""
        if value < 1:
            raise serializers.ValidationError(
                "Duration must be at least 1 day")
        if value > 30:
            raise serializers.ValidationError("Duration cannot exceed 30 days")
        return value

    def validate_daily_available_hours(self, value):
        """Validate daily hours"""
        if not 1 <= value <= 24:
            raise serializers.ValidationError(
                "Daily available hours must be between 1 and 24"
            )
        return value
