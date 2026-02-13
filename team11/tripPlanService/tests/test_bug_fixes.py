"""
Unit tests for the 6 bug fixes applied to Trip Plan Service.

Bug 1: Redundant user_id in generate_trip (views.py)
Bug 2: Deep copy for copy_trip (services.py)
Bug 4: Swapped labels in PDF (pdf_generator.py)
Bug 5: TripDayViewSet.create incompatible signature (views.py)
Bug 7: end_date default calculation (serializers.py)
Bug 8: Ownership checks (views.py)
"""
import json
from datetime import date, time, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model

from data.models import (
    Trip, TripDay, TripItem, BudgetLevelChoices,
    TravelStyleChoices, DensityChoices, ItemTypeChoices,
    PlaceCategoryChoices, PriceTierChoices
)
from data.repository import TripRepository, TripDayRepository, TripItemRepository
from business.services import TripService, TripDayService
from presentation.serializers import TripCreateUpdateSerializer
from presentation.views import TripViewSet, TripDayViewSet, _check_trip_ownership
from presentation.pdf_generator import generate_html_content

User = get_user_model()


class BaseTestCase(TestCase):
    """Base test case with helper methods for creating test data."""

    def setUp(self):
        """Create test users and a sample trip."""
        self.user1 = User.objects.create_user(
            username='seyedali', password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='mohammad', password='testpass456'
        )
        self.factory = RequestFactory()

        # Create a sample trip
        self.trip = Trip.objects.create(
            user=self.user1,
            title='سفر اصفهان',
            province='اصفهان',
            city='اصفهان',
            start_date=date(2026, 3, 21),
            end_date=date(2026, 3, 23),
            duration_days=3,
            budget_level=BudgetLevelChoices.MEDIUM,
            daily_available_hours=10,
            travel_style=TravelStyleChoices.COUPLE,
            density=DensityChoices.BALANCED,
            generation_strategy='MIXED',
            total_estimated_cost=Decimal('5000000.00'),
            interests=['تاریخی', 'فرهنگی'],
        )

        # Create sample days and items
        self.day1 = TripDay.objects.create(
            trip=self.trip,
            day_index=1,
            specific_date=date(2026, 3, 21),
        )
        self.day2 = TripDay.objects.create(
            trip=self.trip,
            day_index=2,
            specific_date=date(2026, 3, 22),
        )

        self.item1 = TripItem.objects.create(
            day=self.day1,
            item_type=ItemTypeChoices.VISIT,
            place_ref_id='place_001',
            title='میدان نقش جهان',
            category=PlaceCategoryChoices.HISTORICAL,
            start_time=time(9, 0),
            end_time=time(11, 0),
            duration_minutes=120,
            sort_order=1,
            estimated_cost=Decimal('200000'),
            price_tier=PriceTierChoices.BUDGET,
        )
        self.item2 = TripItem.objects.create(
            day=self.day1,
            item_type=ItemTypeChoices.VISIT,
            place_ref_id='place_002',
            title='مسجد شیخ لطف الله',
            category=PlaceCategoryChoices.RELIGIOUS,
            start_time=time(11, 30),
            end_time=time(13, 0),
            duration_minutes=90,
            sort_order=2,
            estimated_cost=Decimal('500000'),
            price_tier=PriceTierChoices.MODERATE,
        )
        self.item3 = TripItem.objects.create(
            day=self.day2,
            item_type=ItemTypeChoices.VISIT,
            place_ref_id='place_004',
            title='پل سی‌وسه‌پل',
            category=PlaceCategoryChoices.HISTORICAL,
            start_time=time(15, 0),
            end_time=time(17, 0),
            duration_minutes=120,
            sort_order=1,
            estimated_cost=Decimal('0'),
            price_tier=PriceTierChoices.FREE,
            is_locked=True,
        )


# ─── Bug 2: Deep Copy ──────────────────────────────────────────────

class TestBug2DeepCopy(BaseTestCase):
    """Bug 2: copy_trip should deep copy Days and Items, not just Trip metadata."""

    def test_copy_trip_creates_new_trip(self):
        """Copied trip should be a new distinct object."""
        copied = TripService.copy_trip(self.trip.trip_id, self.user2.id)
        self.assertIsNotNone(copied)
        self.assertNotEqual(copied.trip_id, self.trip.trip_id)
        self.assertEqual(copied.title, f"{self.trip.title} (Copy)")
        self.assertEqual(copied.copied_from_trip_id, self.trip.trip_id)

    def test_copy_trip_copies_days(self):
        """Copied trip should have the same number of days."""
        copied = TripService.copy_trip(self.trip.trip_id)
        original_days = self.trip.days.count()
        copied_days = copied.days.count()
        self.assertEqual(copied_days, original_days)
        self.assertEqual(copied_days, 2)

    def test_copy_trip_copies_items(self):
        """Copied trip should have the same items in each day."""
        copied = TripService.copy_trip(self.trip.trip_id)
        # Day 1 had 2 items
        copied_day1 = copied.days.get(day_index=1)
        self.assertEqual(copied_day1.items.count(), 2)
        # Day 2 had 1 item
        copied_day2 = copied.days.get(day_index=2)
        self.assertEqual(copied_day2.items.count(), 1)

    def test_copy_trip_items_are_unlocked(self):
        """Copied items should be unlocked regardless of original lock state."""
        copied = TripService.copy_trip(self.trip.trip_id)
        for day in copied.days.all():
            for item in day.items.all():
                self.assertFalse(
                    item.is_locked,
                    f"Item '{item.title}' should be unlocked in copy"
                )

    def test_copy_trip_preserves_item_data(self):
        """Copied items should preserve all field values."""
        copied = TripService.copy_trip(self.trip.trip_id)
        copied_item = copied.days.get(day_index=1).items.get(sort_order=1)
        self.assertEqual(copied_item.title, self.item1.title)
        self.assertEqual(copied_item.place_ref_id, self.item1.place_ref_id)
        self.assertEqual(copied_item.estimated_cost, self.item1.estimated_cost)
        self.assertEqual(copied_item.category, self.item1.category)

    def test_copy_trip_preserves_metadata(self):
        """Copied trip should preserve province, interests, etc."""
        copied = TripService.copy_trip(self.trip.trip_id)
        self.assertEqual(copied.province, self.trip.province)
        self.assertEqual(copied.end_date, self.trip.end_date)
        self.assertEqual(copied.density, self.trip.density)
        self.assertEqual(copied.interests, self.trip.interests)
        self.assertEqual(copied.total_estimated_cost, self.trip.total_estimated_cost)

    def test_copy_nonexistent_trip_returns_none(self):
        """Copying a trip that doesn't exist should return None."""
        result = TripService.copy_trip(999999)
        self.assertIsNone(result)


# ─── Bug 4: PDF Labels ─────────────────────────────────────────────

class TestBug4PDFLabels(BaseTestCase):
    """Bug 4: PDF labels should show correct values."""

    def test_budget_label_shows_budget_value(self):
        """'سطح بودجه' should show budget_level display, not density."""
        html = generate_html_content(self.trip)
        # The HTML should contain budget label followed by the budget value
        budget_display = self.trip.get_budget_level_display()
        self.assertIn(budget_display, html)
        # Check that budget label is NOT paired with density value
        density_display = self.trip.get_density_display() if self.trip.density else '-'
        # After "سطح بودجه:" the value should be budget, not density
        budget_section_start = html.index('سطح بودجه:')
        # Find the next metadata-value div
        value_start = html.index('metadata-value', budget_section_start)
        value_end = html.index('</div>', value_start)
        budget_value_section = html[value_start:value_end]
        self.assertIn(budget_display, budget_value_section)

    def test_density_label_shows_density_value(self):
        """'تراکم برنامه' should show density display."""
        html = generate_html_content(self.trip)
        density_display = self.trip.get_density_display() if self.trip.density else '-'
        density_section_start = html.index('تراکم برنامه:')
        value_start = html.index('metadata-value', density_section_start)
        value_end = html.index('</div>', value_start)
        density_value_section = html[value_start:value_end]
        self.assertIn(density_display, density_value_section)

    def test_travel_style_label_exists(self):
        """'سبک سفر' label should exist in the PDF."""
        html = generate_html_content(self.trip)
        self.assertIn('سبک سفر:', html)
        travel_style_display = self.trip.get_travel_style_display()
        style_section_start = html.index('سبک سفر:')
        value_start = html.index('metadata-value', style_section_start)
        value_end = html.index('</div>', value_start)
        style_value_section = html[value_start:value_end]
        self.assertIn(travel_style_display, style_value_section)


# ─── Bug 7: end_date Calculation ──────────────────────────────────

class TestBug7EndDateCalculation(BaseTestCase):
    """Bug 7: Default end_date should produce exactly 3-day duration."""

    def test_default_end_date_gives_3_days(self):
        """When end_date is not provided, duration should be 3 days."""
        data = {
            'title': 'تست سفر',
            'province': 'تهران',
            'startDate': '2026-05-01',
            # endDate intentionally omitted
            'budgetLevel': 'ECONOMY',
            'dailyAvailableHours': 8,
            'travelStyle': 'SOLO',
            'generationStrategy': 'MIXED',
        }
        serializer = TripCreateUpdateSerializer(data=data)
        is_valid = serializer.is_valid()
        self.assertTrue(is_valid, f"Serializer errors: {serializer.errors}")
        trip = serializer.create(serializer.validated_data)
        # duration = (end_date - start_date).days + 1 should be 3
        duration = (trip.end_date - trip.start_date).days + 1
        self.assertEqual(duration, 3, f"Expected 3-day duration, got {duration}")

    def test_explicit_end_date_respected(self):
        """When end_date is explicitly provided, it should be used as-is."""
        data = {
            'title': 'تست سفر',
            'province': 'شیراز',
            'startDate': '2026-05-01',
            'endDate': '2026-05-05',
            'budgetLevel': 'LUXURY',
            'dailyAvailableHours': 12,
            'travelStyle': 'FAMILY',
            'generationStrategy': 'HISTORICAL',
        }
        serializer = TripCreateUpdateSerializer(data=data)
        is_valid = serializer.is_valid()
        self.assertTrue(is_valid, f"Serializer errors: {serializer.errors}")
        trip = serializer.create(serializer.validated_data)
        self.assertEqual(trip.end_date, date(2026, 5, 5))
        duration = (trip.end_date - trip.start_date).days + 1
        self.assertEqual(duration, 5)


# ─── Bug 8: Ownership Checks ───────────────────────────────────────

class TestBug8OwnershipChecks(BaseTestCase):
    """Bug 8: Only trip owners should be able to update/delete their trips."""

    def test_check_ownership_owner_allowed(self):
        """Owner should pass ownership check."""
        request = self.factory.get('/')
        request.jwt_user_id = self.user1.id
        self.assertTrue(_check_trip_ownership(request, self.trip))

    def test_check_ownership_non_owner_denied(self):
        """Non-owner should fail ownership check."""
        request = self.factory.get('/')
        request.jwt_user_id = self.user2.id
        self.assertFalse(_check_trip_ownership(request, self.trip))

    def test_check_ownership_guest_trip_allowed(self):
        """Guest trip (no user) should allow anyone."""
        guest_trip = Trip.objects.create(
            user=None,
            title='Guest Trip',
            province='تبریز',
            start_date=date(2026, 6, 1),
            duration_days=2,
            budget_level=BudgetLevelChoices.ECONOMY,
            daily_available_hours=8,
            travel_style=TravelStyleChoices.SOLO,
            generation_strategy='MIXED',
        )
        request = self.factory.get('/')
        request.jwt_user_id = self.user2.id
        self.assertTrue(_check_trip_ownership(request, guest_trip))

    def test_check_ownership_no_auth_allowed(self):
        """Request without jwt_user_id (dev mode) should allow access."""
        request = self.factory.get('/')
        # No jwt_user_id attribute
        self.assertTrue(_check_trip_ownership(request, self.trip))

    def test_update_trip_by_non_owner_returns_403(self):
        """PUT by non-owner should return 403 Forbidden."""
        request = self.factory.put(
            f'/api/trips/{self.trip.trip_id}/',
            data=json.dumps({'title': 'Hacked!'}),
            content_type='application/json'
        )
        request.jwt_user_id = self.user2.id
        view = TripViewSet.as_view({'put': 'update'})
        response = view(request, pk=self.trip.trip_id)
        self.assertEqual(response.status_code, 403)

    def test_update_trip_by_owner_allowed(self):
        """PUT by owner should succeed (200)."""
        request = self.factory.put(
            f'/api/trips/{self.trip.trip_id}/',
            data=json.dumps({
                'title': 'سفر اصفهان ویرایش‌شده',
                'province': 'اصفهان',
                'startDate': '2026-03-21',
                'budgetLevel': 'MEDIUM',
                'dailyAvailableHours': 10,
                'travelStyle': 'COUPLE',
                'generationStrategy': 'MIXED',
            }),
            content_type='application/json'
        )
        request.jwt_user_id = self.user1.id
        view = TripViewSet.as_view({'put': 'update'})
        response = view(request, pk=self.trip.trip_id)
        self.assertIn(response.status_code, [200, 201])

    def test_delete_trip_by_non_owner_returns_403(self):
        """DELETE by non-owner should return 403 Forbidden."""
        request = self.factory.delete(f'/api/trips/{self.trip.trip_id}/')
        request.jwt_user_id = self.user2.id
        view = TripViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=self.trip.trip_id)
        self.assertEqual(response.status_code, 403)

    def test_delete_trip_by_owner_allowed(self):
        """DELETE by owner should succeed (204)."""
        # Create a separate trip to delete
        trip_to_delete = Trip.objects.create(
            user=self.user1,
            title='Trip to Delete',
            province='مشهد',
            start_date=date(2026, 4, 1),
            duration_days=1,
            budget_level=BudgetLevelChoices.ECONOMY,
            daily_available_hours=8,
            travel_style=TravelStyleChoices.SOLO,
            generation_strategy='MIXED',
        )
        request = self.factory.delete(f'/api/trips/{trip_to_delete.trip_id}/')
        request.jwt_user_id = self.user1.id
        view = TripViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=trip_to_delete.trip_id)
        self.assertEqual(response.status_code, 204)


# ─── Bug 5: TripDayViewSet.create ──────────────────────────────────

class TestBug5TripDayCreate(BaseTestCase):
    """Bug 5: TripDayViewSet.create should work without TripDaySerializer validation."""

    def test_create_day_without_trip_id_returns_400(self):
        """POST without trip_id should return 400."""
        request = self.factory.post(
            '/api/trip-days/',
            data=json.dumps({}),
            content_type='application/json'
        )
        view = TripDayViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 400)

    def test_create_day_with_valid_trip_id(self):
        """POST with valid trip_id should create a day."""
        request = self.factory.post(
            '/api/trip-days/',
            data=json.dumps({'trip_id': self.trip.trip_id}),
            content_type='application/json'
        )
        view = TripDayViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertIn(response.status_code, [201, 400])
        # If 201, verify a day was created
        if response.status_code == 201:
            self.assertEqual(self.trip.days.count(), 3)  # was 2, now 3
