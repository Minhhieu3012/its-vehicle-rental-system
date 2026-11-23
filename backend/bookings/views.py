import json
from datetime import date

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from vehicles.models import Vehicle

from .models import Booking
from .utils import (
    calculate_dynamic_pricing,
    is_overlapping,
    sync_vehicle_status_after_booking_change,
)


def is_admin(user):
    return user.is_authenticated and user.is_staff


@csrf_exempt
@login_required
def create_booking(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        vehicle_id = int(payload["vehicle_id"])
        start_date = payload["start_date"]
        end_date = payload["end_date"]
    except Exception:
        return JsonResponse({"detail": "Invalid JSON/body"}, status=400)

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    try:
        s = date.fromisoformat(start_date)
        e = date.fromisoformat(end_date)
    except Exception:
        return JsonResponse({"detail": "start_date/end_date phải dạng YYYY-MM-DD"}, status=400)

    if e < s:
        return JsonResponse({"detail": "end_date phải >= start_date"}, status=400)

    # Chỉ chặn nếu xe đang bảo trì; các trường hợp khác kiểm tra trùng lịch bên dưới
    if vehicle.status == Vehicle.STATUS_MAINTENANCE:
        return JsonResponse({"detail": "Xe đang bảo trì, không thể đặt lúc này"}, status=400)

    if is_overlapping(vehicle, s, e):
        return JsonResponse({"detail": "Xe bị trùng lịch"}, status=400)

    pricing = calculate_dynamic_pricing(vehicle, s, e, include_tax=True)

    booking = Booking.objects.create(
        customer=request.user,
        vehicle=vehicle,
        start_date=s,
        end_date=e,
        total_price=pricing["final_total"],
        status="pending",
    )

    if vehicle.status == Vehicle.STATUS_AVAILABLE:
        vehicle.status = Vehicle.STATUS_BOOKED
        vehicle.save(update_fields=["status"])

    return JsonResponse({
        "id": booking.id,
        "status": booking.status,
        "total_price": str(booking.total_price),
        "vehicle_id": booking.vehicle_id,
        "vehicle_status": vehicle.status,
        "start_date": str(booking.start_date),
        "end_date": str(booking.end_date),
        "pricing": {
            "days": pricing["days"],
            "base_total": str(pricing["base_total"]),
            "peak_surcharge": str(pricing["peak_surcharge"]),
            "peak_surcharge_percent": pricing["peak_surcharge_percent"],
            "demand_surcharge": str(pricing["demand_surcharge"]),
            "demand_surcharge_percent": pricing["demand_surcharge_percent"],
            "occupancy_percent": pricing["occupancy_percent"],
            "tax_fee": str(pricing["tax_fee"]),
            "final_total": str(pricing["final_total"]),
        },
    }, status=201)


@login_required
def my_bookings(request):
    qs = Booking.objects.filter(customer=request.user).select_related("vehicle").order_by("-id")
    data = []
    for b in qs:
        data.append({
            "id": b.id,
            "status": b.status,
            "total_price": str(b.total_price),
            "vehicle": {
                "id": b.vehicle_id,
                "license_plate": getattr(b.vehicle, "license_plate", ""),
                "name": getattr(b.vehicle, "name", ""),
                "status": b.vehicle.status,
            },
            "start_date": str(b.start_date),
            "end_date": str(b.end_date),
        })
    return JsonResponse(data, safe=False)


@csrf_exempt
@login_required
def cancel_booking(request, booking_id: int):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    b = get_object_or_404(Booking, id=booking_id)

    if (not request.user.is_staff) and b.customer_id != request.user.id:
        return JsonResponse({"detail": "Không có quyền huỷ booking này"}, status=403)

    if b.status not in ("pending", "approved"):
        return JsonResponse({"detail": "Không thể huỷ ở trạng thái này"}, status=400)

    b.status = "cancelled"
    b.save(update_fields=["status"])

    vehicle_status = sync_vehicle_status_after_booking_change(b.vehicle)

    return JsonResponse({"id": b.id, "status": b.status, "vehicle_status": vehicle_status})


@csrf_exempt
@user_passes_test(is_admin)
def approve_booking(request, booking_id: int):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    b = get_object_or_404(Booking, id=booking_id)

    if b.status != "pending":
        return JsonResponse({"detail": "Chỉ duyệt booking pending"}, status=400)

    b.status = "approved"
    b.save(update_fields=["status"])

    v = b.vehicle
    v.status = Vehicle.STATUS_IN_USE
    v.save(update_fields=["status"])

    return JsonResponse({"id": b.id, "status": b.status, "vehicle_status": v.status})


@csrf_exempt
@user_passes_test(is_admin)
def complete_booking(request, booking_id: int):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    b = get_object_or_404(Booking, id=booking_id)

    if b.status != "approved":
        return JsonResponse({"detail": "Chỉ complete booking approved"}, status=400)

    b.status = "completed"
    b.save(update_fields=["status"])

    vehicle_status = sync_vehicle_status_after_booking_change(b.vehicle)

    return JsonResponse({"id": b.id, "status": b.status, "vehicle_status": vehicle_status})
