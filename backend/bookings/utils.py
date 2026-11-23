from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Q
from django.utils import timezone

ACTIVE_STATUSES = ("pending", "approved")

WEEKEND_SURCHARGE_RATE = Decimal("0.20")       # +20% vào Thứ 7 / Chủ nhật
PEAK_HOUR_SURCHARGE_RATE = Decimal("0.10")     # +10% khi đặt vào giờ cao điểm (7-9h, 17-19h)
PEAK_HOUR_RANGES = ((7, 9), (17, 19))
DEMAND_HIGH_THRESHOLD = Decimal("0.70")        # >= 70% đội xe đang hoạt động/đã đặt -> +15%
DEMAND_HIGH_SURCHARGE_RATE = Decimal("0.15")
DEMAND_MEDIUM_THRESHOLD = Decimal("0.50")      # >= 50% đội xe đang hoạt động/đã đặt -> +10%
DEMAND_MEDIUM_SURCHARGE_RATE = Decimal("0.10")
TAX_RATE = Decimal("0.10")                     # 10% thuế & phí dịch vụ


def _quantize_money(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def dates_in_range(start: date, end: date):
    """
    Yield từng ngày tính phí thuê xe.
    - Nếu thuê và trả cùng ngày (start == end): tính 1 ngày.
    - Nếu end > start: tính theo số ngày chênh lệch (start -> end - 1),
      đồng bộ với chuẩn thuê theo chu kỳ 24h trên giao diện.
    """
    if end < start:
        return
    total_days = (end - start).days
    if total_days == 0:
        yield start
        return
    for offset in range(total_days):
        yield start + timedelta(days=offset)


def is_weekend(d: date) -> bool:
    """Trả về True nếu là Thứ 7 (5) hoặc Chủ nhật (6)."""
    return d.weekday() >= 5


def is_peak_hour(reference_dt: datetime | None = None) -> bool:
    """Kiểm tra giờ cao điểm giao thông (07:00-09:00 và 17:00-19:00 giờ địa phương)."""
    dt = reference_dt if reference_dt is not None else timezone.localtime()
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    hour = dt.hour
    return any(start_h <= hour < end_h for start_h, end_h in PEAK_HOUR_RANGES)


def get_fleet_occupancy_rate() -> Decimal:
    """
    Tính tỷ lệ lấp đầy đội xe theo thời gian thực (Demand-based ITS):
    occupied (booked + in_use) / tổng số xe khả dụng (loại trừ xe đang bảo trì).
    """
    from vehicles.models import Vehicle

    operational_qs = Vehicle.objects.exclude(status=Vehicle.STATUS_MAINTENANCE)
    total_operational = operational_qs.count()
    if total_operational == 0:
        return Decimal("0.00")

    occupied_count = operational_qs.filter(
        status__in=[Vehicle.STATUS_BOOKED, Vehicle.STATUS_IN_USE]
    ).count()
    return (Decimal(occupied_count) / Decimal(total_operational)).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP
    )


def get_demand_surcharge_rate(occupancy_rate: Decimal) -> Decimal:
    """Trả về mức phụ phí theo tỷ lệ lấp đầy đội xe."""
    if occupancy_rate >= DEMAND_HIGH_THRESHOLD:
        return DEMAND_HIGH_SURCHARGE_RATE
    if occupancy_rate >= DEMAND_MEDIUM_THRESHOLD:
        return DEMAND_MEDIUM_SURCHARGE_RATE
    return Decimal("0.00")


def get_unit_price_per_day(vehicle) -> Decimal:
    """Lấy đơn giá theo ngày từ vehicle."""
    if hasattr(vehicle, "price_per_day") and vehicle.price_per_day is not None:
        return Decimal(str(vehicle.price_per_day))
    if hasattr(vehicle, "price_per_hour") and vehicle.price_per_hour is not None:
        return _quantize_money(Decimal(str(vehicle.price_per_hour)) * Decimal("24"))
    return Decimal("0.00")


def calculate_dynamic_pricing(
    vehicle,
    start_date: date,
    end_date: date,
    include_tax: bool = True,
    reference_dt: datetime | None = None,
    occupancy_rate: Decimal | None = None,
) -> dict:
    """
    Thuật toán ITS Dynamic Pricing thống nhất cho toàn hệ thống:
    1. Time-based:
       - Cuối tuần (T7/CN): +20% trên đơn giá ngày đó.
       - Giờ cao điểm (07:00-09:00, 17:00-19:00): +10% trên tiền thuê cơ bản.
    2. Demand-based:
       - Dựa trên tỷ lệ lấp đầy đội xe (occupancy >= 50%: +10%, >= 70%: +15%).
    3. Thuế & phí dịch vụ: 10% (nếu include_tax=True).
    """
    daily_rate = get_unit_price_per_day(vehicle)
    weekend_rate = _quantize_money(daily_rate * (Decimal("1.00") + WEEKEND_SURCHARGE_RATE))

    if end_date < start_date:
        zero = Decimal("0.00")
        return {
            "days": 0,
            "weekday_count": 0,
            "weekend_count": 0,
            "daily_rate": daily_rate,
            "weekend_rate": weekend_rate,
            "weekday_total": zero,
            "weekend_total": zero,
            "base_total": zero,
            "is_peak_hour": False,
            "peak_surcharge_rate": zero,
            "peak_surcharge_percent": 0,
            "peak_surcharge": zero,
            "occupancy_rate": zero,
            "occupancy_percent": 0.0,
            "demand_surcharge_rate": zero,
            "demand_surcharge_percent": 0,
            "demand_surcharge": zero,
            "subtotal_before_tax": zero,
            "tax_fee": zero,
            "final_total": zero,
        }

    weekday_count = 0
    weekend_count = 0
    for d in dates_in_range(start_date, end_date):
        if is_weekend(d):
            weekend_count += 1
        else:
            weekday_count += 1

    weekday_total = _quantize_money(daily_rate * Decimal(weekday_count))
    weekend_total = _quantize_money(weekend_rate * Decimal(weekend_count))
    base_total = _quantize_money(weekday_total + weekend_total)

    peak_active = is_peak_hour(reference_dt)
    peak_rate = PEAK_HOUR_SURCHARGE_RATE if peak_active else Decimal("0.00")
    peak_surcharge = _quantize_money(base_total * peak_rate)

    occ_rate = occupancy_rate if occupancy_rate is not None else get_fleet_occupancy_rate()
    demand_rate = get_demand_surcharge_rate(occ_rate)
    demand_surcharge = _quantize_money(base_total * demand_rate)

    subtotal_before_tax = _quantize_money(base_total + peak_surcharge + demand_surcharge)
    tax_fee = _quantize_money(subtotal_before_tax * TAX_RATE) if include_tax else Decimal("0.00")
    final_total = _quantize_money(subtotal_before_tax + tax_fee)

    return {
        "days": weekday_count + weekend_count,
        "weekday_count": weekday_count,
        "weekend_count": weekend_count,
        "daily_rate": daily_rate,
        "weekend_rate": weekend_rate,
        "weekday_total": weekday_total,
        "weekend_total": weekend_total,
        "base_total": base_total,
        "is_peak_hour": peak_active,
        "peak_surcharge_rate": peak_rate,
        "peak_surcharge_percent": int(peak_rate * 100),
        "peak_surcharge": peak_surcharge,
        "occupancy_rate": occ_rate,
        "occupancy_percent": round(float(occ_rate * 100), 1),
        "demand_surcharge_rate": demand_rate,
        "demand_surcharge_percent": int(demand_rate * 100),
        "demand_surcharge": demand_surcharge,
        "subtotal_before_tax": subtotal_before_tax,
        "tax_fee": tax_fee,
        "final_total": final_total,
    }


def calc_total_price(
    vehicle,
    start_date: date,
    end_date: date,
    include_tax: bool = True,
    reference_dt: datetime | None = None,
    occupancy_rate: Decimal | None = None,
) -> Decimal:
    """Tính tổng tiền theo thuật toán Dynamic Pricing thống nhất."""
    breakdown = calculate_dynamic_pricing(
        vehicle=vehicle,
        start_date=start_date,
        end_date=end_date,
        include_tax=include_tax,
        reference_dt=reference_dt,
        occupancy_rate=occupancy_rate,
    )
    return breakdown["final_total"]


def is_overlapping(vehicle, start_date: date, end_date: date, exclude_booking_id: int | None = None) -> bool:
    """
    Kiểm tra trùng lịch: existing.start <= new.end AND existing.end >= new.start.
    Chỉ xét các booking đang hoạt động (pending/approved).
    """
    qs = vehicle.bookings.filter(status__in=ACTIVE_STATUSES).filter(
        Q(start_date__lte=end_date) & Q(end_date__gte=start_date)
    )
    if exclude_booking_id is not None:
        qs = qs.exclude(id=exclude_booking_id)
    return qs.exists()


def sync_vehicle_status_after_booking_change(vehicle) -> str:
    """
    Đồng bộ trạng thái xe sau khi booking bị hủy hoặc hoàn thành:
    - Giữ nguyên nếu xe đang 'maintenance'.
    - Nếu vẫn còn booking 'approved' -> 'in_use'.
    - Nếu vẫn còn booking 'pending' -> 'booked'.
    - Ngược lại -> 'available'.
    """
    from vehicles.models import Vehicle

    if vehicle.status == Vehicle.STATUS_MAINTENANCE:
        return vehicle.status

    if vehicle.bookings.filter(status="approved").exists():
        new_status = Vehicle.STATUS_IN_USE
    elif vehicle.bookings.filter(status="pending").exists():
        new_status = Vehicle.STATUS_BOOKED
    else:
        new_status = Vehicle.STATUS_AVAILABLE

    if vehicle.status != new_status:
        vehicle.status = new_status
        vehicle.save(update_fields=["status"])
    return vehicle.status


def forecast_monthly_revenue(monthly_revenues: list[float], current_month: int) -> dict:
    """
    Dự báo doanh thu theo tháng bằng hồi quy tuyến tính (Ordinary Least Squares)
    dựa trên dữ liệu thực tế từ tháng 1 đến tháng hiện tại.
    Trả về mảng 12 giá trị dự báo (chỉ điền từ tháng hiện tại trở đi để vẽ đường dự báo nối tiếp),
    dự báo tháng kế tiếp và tổng doanh thu dự kiến cả năm.
    """
    observed_count = max(1, min(12, current_month))
    observed = [float(monthly_revenues[i]) for i in range(observed_count)]
    non_zero_points = [(i + 1, val) for i, val in enumerate(observed) if val > 0]

    if not non_zero_points:
        return {
            "forecast_series": [None] * 12,
            "next_month_forecast": 0.0,
            "projected_annual_revenue": 0.0,
            "trend_direction": "flat",
        }

    if len(non_zero_points) == 1:
        slope = 0.0
        intercept = non_zero_points[0][1]
    else:
        xs = [p[0] for p in non_zero_points]
        ys = [p[1] for p in non_zero_points]
        n = len(xs)
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        denom = sum((x - mean_x) ** 2 for x in xs)
        if denom == 0:
            slope = 0.0
            intercept = mean_y
        else:
            slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denom
            intercept = mean_y - slope * mean_x

    def predict(month_idx: int) -> float:
        return round(max(0.0, intercept + slope * month_idx), 2)

    forecast_series: list[float | None] = [None] * 12
    # Neo điểm nối từ tháng hiện tại để đường dự báo liên mạch trên Chart.js
    forecast_series[observed_count - 1] = round(observed[observed_count - 1], 2)
    projected_remaining = 0.0
    for m in range(observed_count + 1, 13):
        pred = predict(m)
        forecast_series[m - 1] = pred
        projected_remaining += pred

    next_month_idx = observed_count + 1 if observed_count < 12 else 13
    next_month_forecast = predict(next_month_idx)
    projected_annual_revenue = round(sum(observed) + projected_remaining, 2)

    if slope > 1e-6:
        trend_direction = "up"
    elif slope < -1e-6:
        trend_direction = "down"
    else:
        trend_direction = "flat"

    return {
        "forecast_series": forecast_series,
        "next_month_forecast": next_month_forecast,
        "projected_annual_revenue": projected_annual_revenue,
        "trend_direction": trend_direction,
    }
