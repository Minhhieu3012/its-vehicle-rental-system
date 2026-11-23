import json
from datetime import date, datetime
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from vehicles.models import Vehicle
from bookings.models import Booking
from bookings.utils import (
    calculate_dynamic_pricing,
    forecast_monthly_revenue,
    get_fleet_occupancy_rate,
    is_overlapping,
)

User = get_user_model()


class VehicleStatusAndBookingSyncTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = User.objects.create_user(username="customer1", password="password123")
        self.other_user = User.objects.create_user(username="customer2", password="password123")
        self.admin = User.objects.create_user(username="admin1", password="password123", is_staff=True)

        self.vehicle = Vehicle.objects.create(
            name="VinFast VF8",
            license_plate="51K-123.45",
            vehicle_type="car_4",
            price_per_day=Decimal("1000000.00"),
            latitude=10.762622,
            longitude=106.660172,
        )

    def test_vehicle_default_status_is_lowercase_available(self):
        self.assertEqual(self.vehicle.status, Vehicle.STATUS_AVAILABLE)
        self.assertEqual(self.vehicle.status, "available")

    def test_booking_api_lifecycle_uses_customer_and_canonical_statuses(self):
        self.client.login(username="customer1", password="password123")

        # 1. Create booking via API
        resp = self.client.post(
            reverse("bookings:create_booking"),
            data=json.dumps({
                "vehicle_id": self.vehicle.id,
                "start_date": "2026-12-01",
                "end_date": "2026-12-03",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        payload = resp.json()
        booking_id = payload["id"]
        self.assertEqual(payload["status"], "pending")
        self.assertEqual(payload["vehicle_status"], Vehicle.STATUS_BOOKED)
        self.assertIn("pricing", payload)

        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.status, Vehicle.STATUS_BOOKED)

        # 2. My bookings API returns customer's booking
        my_resp = self.client.get(reverse("bookings:my_bookings"))
        self.assertEqual(my_resp.status_code, 200)
        items = my_resp.json()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], booking_id)

        # 3. Overlapping booking via API is rejected
        overlap_resp = self.client.post(
            reverse("bookings:create_booking"),
            data=json.dumps({
                "vehicle_id": self.vehicle.id,
                "start_date": "2026-12-02",
                "end_date": "2026-12-04",
            }),
            content_type="application/json",
        )
        self.assertEqual(overlap_resp.status_code, 400)

        # 4. Another user cannot cancel customer1's booking
        self.client.login(username="customer2", password="password123")
        forbid_resp = self.client.post(reverse("bookings:cancel_booking", args=[booking_id]))
        self.assertEqual(forbid_resp.status_code, 403)

        # 5. Admin approves booking -> vehicle becomes 'in_use'
        self.client.login(username="admin1", password="password123")
        approve_resp = self.client.post(reverse("bookings:approve_booking", args=[booking_id]))
        self.assertEqual(approve_resp.status_code, 200)
        self.assertEqual(approve_resp.json()["vehicle_status"], Vehicle.STATUS_IN_USE)

        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.status, Vehicle.STATUS_IN_USE)

        # 6. Admin completes booking -> vehicle returns to 'available'
        complete_resp = self.client.post(reverse("bookings:complete_booking", args=[booking_id]))
        self.assertEqual(complete_resp.status_code, 200)
        self.assertEqual(complete_resp.json()["vehicle_status"], Vehicle.STATUS_AVAILABLE)

        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.status, Vehicle.STATUS_AVAILABLE)

    def test_frontend_payment_blocks_overlapping_and_syncs_status(self):
        Booking.objects.create(
            customer=self.other_user,
            vehicle=self.vehicle,
            start_date=date(2026, 12, 10),
            end_date=date(2026, 12, 12),
            total_price=Decimal("2200000.00"),
            status="approved",
        )

        self.client.login(username="customer1", password="password123")
        # Attempt overlapping booking on frontend payment page
        resp = self.client.post(
            reverse("frontend:vehicle_payment", args=[self.vehicle.id]),
            {
                "pickup_date": "2026-12-11",
                "return_date": "2026-12-13",
                "payment_method": "credit_card",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            Booking.objects.filter(customer=self.customer, vehicle=self.vehicle).count(),
            0,
        )

        # Non-overlapping booking succeeds
        resp_ok = self.client.post(
            reverse("frontend:vehicle_payment", args=[self.vehicle.id]),
            {
                "pickup_date": "2026-12-15",
                "return_date": "2026-12-17",
                "payment_method": "credit_card",
            },
        )
        self.assertEqual(resp_ok.status_code, 302)
        self.assertEqual(
            Booking.objects.filter(customer=self.customer, vehicle=self.vehicle).count(),
            1,
        )


class ITSDynamicPricingAndAnalyticsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username="admin_stats", password="password123", is_staff=True)
        self.customer = User.objects.create_user(username="cust_stats", password="password123")

        self.v1 = Vehicle.objects.create(
            name="Xe 1", license_plate="51A-000.01", vehicle_type="car_4",
            price_per_day=Decimal("1000000.00"), status=Vehicle.STATUS_AVAILABLE,
            latitude=10.77, longitude=106.66,
        )
        self.v2 = Vehicle.objects.create(
            name="Xe 2", license_plate="51A-000.02", vehicle_type="bike",
            price_per_day=Decimal("200000.00"), status=Vehicle.STATUS_IN_USE,
            latitude=10.78, longitude=106.67,
        )
        self.v3 = Vehicle.objects.create(
            name="Xe 3", license_plate="51A-000.03", vehicle_type="car_7",
            price_per_day=Decimal("1500000.00"), status=Vehicle.STATUS_BOOKED,
            latitude=10.79, longitude=106.68,
        )

    def test_dynamic_pricing_weekend_peak_and_demand(self):
        # 2 of 3 operational vehicles are booked/in_use -> 66.67% occupancy -> +10% demand surcharge
        occ = get_fleet_occupancy_rate()
        self.assertGreaterEqual(occ, Decimal("0.50"))
        self.assertLess(occ, Decimal("0.70"))

        # Friday 2026-11-27 -> Sunday 2026-11-29 (1 weekday + 1 weekend day: Fri & Sat)
        # Peak hour reference: 08:00 (+10%)
        pricing = calculate_dynamic_pricing(
            vehicle=self.v1,
            start_date=date(2026, 11, 27),
            end_date=date(2026, 11, 29),
            include_tax=True,
            reference_dt=datetime(2026, 11, 24, 8, 30),
        )
        self.assertEqual(pricing["days"], 2)
        self.assertEqual(pricing["weekday_count"], 1)
        self.assertEqual(pricing["weekend_count"], 1)
        # Base: 1,000,000 + 1,200,000 = 2,200,000
        self.assertEqual(pricing["base_total"], Decimal("2200000.00"))
        # Peak (+10%): 220,000; Demand (+10%): 220,000 -> subtotal 2,640,000; tax 10% = 264,000; total = 2,904,000
        self.assertTrue(pricing["is_peak_hour"])
        self.assertEqual(pricing["peak_surcharge"], Decimal("220000.00"))
        self.assertEqual(pricing["demand_surcharge"], Decimal("220000.00"))
        self.assertEqual(pricing["tax_fee"], Decimal("264000.00"))
        self.assertEqual(pricing["final_total"], Decimal("2904000.00"))

    def test_revenue_forecast_trend(self):
        monthly = [1000000, 2000000, 3000000, 4000000, 0, 0, 0, 0, 0, 0, 0, 0]
        result = forecast_monthly_revenue(monthly, current_month=4)
        self.assertEqual(result["trend_direction"], "up")
        self.assertAlmostEqual(result["next_month_forecast"], 5000000.0, places=1)
        self.assertAlmostEqual(result["forecast_series"][4], 5000000.0, places=1)

    def test_map_and_admin_analytics_pages_render(self):
        # Map page with heatmap control & occupancy
        map_resp = self.client.get(reverse("frontend:map"))
        self.assertEqual(map_resp.status_code, 200)
        self.assertContains(map_resp, "toggle-heatmap-btn")
        self.assertContains(map_resp, "leaflet-heat.js")

        # Admin analytics page with forecast & frequency charts
        Booking.objects.create(
            customer=self.customer,
            vehicle=self.v1,
            start_date=date(2026, 1, 15),
            end_date=date(2026, 1, 17),
            total_price=Decimal("2200000.00"),
            status="completed",
        )
        self.client.login(username="admin_stats", password="password123")
        stats_resp = self.client.get(reverse("frontend:admin_stats"))
        self.assertEqual(stats_resp.status_code, 200)
        self.assertContains(stats_resp, "revenueChart")
        self.assertContains(stats_resp, "frequencyChart")
        self.assertContains(stats_resp, "vehicleTypeChart")
