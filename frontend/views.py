from decimal import Decimal
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q, Sum, Avg, Count
from django.db.models.functions import ExtractMonth
from django.http import JsonResponse

from .forms import (
    RegistrationForm, UserLoginForm,
    ReviewForm, VehicleForm
)

from vehicles.models import Vehicle
from bookings.models import Booking
from bookings.utils import (
    calculate_dynamic_pricing,
    forecast_monthly_revenue,
    get_fleet_occupancy_rate,
    is_overlapping,
    sync_vehicle_status_after_booking_change,
)
from reviews.models import Review


def is_admin(user):
    return user.is_authenticated and user.is_staff


# ==========================================
# 1. PUBLIC VIEWS (DÀNH CHO MỌI NGƯỜI)
# ==========================================

def home(request):
    vehicles = Vehicle.objects.all().order_by('-id')

    vehicle_name = request.GET.get('q')
    vehicle_type = request.GET.get('type')

    if vehicle_name:
        vehicles = vehicles.filter(name__icontains=vehicle_name)
    if vehicle_type:
        vehicles = vehicles.filter(vehicle_type=vehicle_type)

    return render(request, 'pages/home.html', {'featured_vehicles': vehicles[:8]})


def map_view(request):
    vehicles = Vehicle.objects.exclude(
        Q(latitude__isnull=True) | Q(longitude__isnull=True)
    ).annotate(
        avg_rating=Avg('reviews__rating'),
        completed_trips=Count('bookings', filter=Q(bookings__status='completed'), distinct=True),
    )

    vehicles_json = []
    for v in vehicles:
        vehicles_json.append({
            'id': v.id,
            'name': v.name,
            'plate': v.license_plate,
            'lat': float(v.latitude),
            'lng': float(v.longitude),
            'status': v.status,
            'status_display': v.get_status_display(),
            'image_url': v.image.url if v.image else '/static/img/placeholder.jpg',
            'detail_url': reverse('frontend:vehicle_detail', args=[v.id]),
            'price': float(v.price_per_day),
            'rating': round(v.avg_rating, 1) if v.avg_rating else 5.0,
            'trips': v.completed_trips,
        })

    occupancy_percent = round(float(get_fleet_occupancy_rate() * 100), 1)
    return render(request, 'pages/map.html', {
        'vehicles': vehicles,
        'vehicles_json': vehicles_json,
        'occupancy_percent': occupancy_percent,
    })


def vehicle_list(request):
    vehicles = Vehicle.objects.all()

    vehicle_type = request.GET.get('vehicle_type')
    if vehicle_type:
        vehicles = vehicles.filter(vehicle_type=vehicle_type)

    sort_by = request.GET.get('sort')
    if sort_by == 'price_asc':
        vehicles = vehicles.order_by('price_per_day')
    elif sort_by == 'price_desc':
        vehicles = vehicles.order_by('-price_per_day')
    else:
        vehicles = vehicles.order_by('-id')

    return render(request, 'vehicles/list.html', {'vehicles': vehicles})


def vehicle_detail(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    reviews = Review.objects.filter(vehicle=vehicle).order_by('-created_at')

    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    avg_rating = round(avg_rating, 1) if avg_rating else 0
    review_count = reviews.count()

    return render(request, 'vehicles/detail.html', {
        'vehicle': vehicle,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'review_count': review_count,
    })


# ==========================================
# 2. USER OPERATIONS (DÀNH CHO NGƯỜI THUÊ)
# ==========================================

@login_required(login_url='frontend:login')
def vehicle_payment(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)

    if vehicle.status == Vehicle.STATUS_MAINTENANCE:
        messages.error(request, "Xe hiện đang bảo trì, không thể đặt vào lúc này.")
        return redirect('frontend:vehicle_detail', vehicle_id=vehicle.id)

    pickup_str = request.POST.get('pickup_date') or request.GET.get('pickup_date', '')
    return_str = request.POST.get('return_date') or request.GET.get('return_date', '')

    try:
        p_date = datetime.strptime(pickup_str.split(',')[0].strip(), "%Y-%m-%d").date()
        r_date = datetime.strptime(return_str.split(',')[0].strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError, IndexError, TypeError):
        p_date = datetime.now().date()
        r_date = p_date + timedelta(days=1)

    if r_date < p_date:
        messages.error(request, "Ngày trả xe phải lớn hơn hoặc bằng ngày nhận xe.")
        return redirect('frontend:vehicle_detail', vehicle_id=vehicle.id)

    if is_overlapping(vehicle, p_date, r_date):
        messages.error(
            request,
            f"Xe đã có lịch đặt trong khoảng {p_date.strftime('%d/%m/%Y')} - {r_date.strftime('%d/%m/%Y')}. Vui lòng chọn ngày khác."
        )
        return redirect('frontend:vehicle_detail', vehicle_id=vehicle.id)

    pricing = calculate_dynamic_pricing(vehicle, p_date, r_date, include_tax=True)

    # Xử lý xác nhận thanh toán
    if request.method == 'POST' and 'payment_method' in request.POST:
        try:
            if is_overlapping(vehicle, p_date, r_date):
                messages.error(request, "Rất tiếc, lịch xe vừa được người khác đặt. Vui lòng chọn ngày khác.")
                return redirect('frontend:vehicle_detail', vehicle_id=vehicle.id)

            Booking.objects.create(
                customer=request.user,
                vehicle=vehicle,
                start_date=p_date,
                end_date=r_date,
                total_price=pricing['final_total'],
                status='pending'
            )
            if vehicle.status == Vehicle.STATUS_AVAILABLE:
                vehicle.status = Vehicle.STATUS_BOOKED
                vehicle.save(update_fields=['status'])

            messages.success(request, "Thanh toán thành công! Đơn hàng đang chờ xác nhận.")
            return redirect('frontend:order_list')
        except Exception as e:
            messages.error(request, f"Lỗi hệ thống: {str(e)}")
            return redirect('frontend:vehicle_detail', vehicle_id=vehicle.id)

    return render(request, 'bookings/payment.html', {
        'vehicle': vehicle,
        'pickup_date': p_date,
        'return_date': r_date,
        'days': pricing['days'],
        'weekday_count': pricing['weekday_count'],
        'weekend_count': pricing['weekend_count'],
        'weekday_total': pricing['weekday_total'],
        'weekend_total': pricing['weekend_total'],
        'weekend_rate': pricing['weekend_rate'],
        'is_peak_hour': pricing['is_peak_hour'],
        'peak_surcharge_percent': pricing['peak_surcharge_percent'],
        'peak_surcharge': pricing['peak_surcharge'],
        'occupancy_percent': pricing['occupancy_percent'],
        'demand_surcharge_percent': pricing['demand_surcharge_percent'],
        'demand_surcharge': pricing['demand_surcharge'],
        'tax_fee': pricing['tax_fee'],
        'final_total': pricing['final_total'],
    })


@login_required(login_url='frontend:login')
def order_list(request):
    try:
        bookings_qs = Booking.objects.filter(customer=request.user).select_related('vehicle').order_by('-id')
        status_filter = request.GET.get('status')
        search_query = request.GET.get('q')

        if status_filter and status_filter != 'all':
            bookings_qs = bookings_qs.filter(status=status_filter)
        if search_query:
            bookings_qs = bookings_qs.filter(
                Q(vehicle__name__icontains=search_query) | Q(vehicle__license_plate__icontains=search_query)
            )

        reviewed_vehicle_ids = list(Review.objects.filter(user=request.user).values_list('vehicle_id', flat=True))

        all_user_bookings = Booking.objects.filter(customer=request.user)
        context = {
            'bookings': bookings_qs,
            'reviewed_vehicle_ids': reviewed_vehicle_ids,
            'active_count': all_user_bookings.filter(status='approved').count(),
            'completed_count': all_user_bookings.filter(status='completed').count(),
            'pending_count': all_user_bookings.filter(status='pending').count(),
        }
    except Exception as e:
        messages.error(request, f"Lỗi hiển thị danh sách: {str(e)}")
        context = {
            'bookings': [],
            'reviewed_vehicle_ids': [],
            'active_count': 0,
            'completed_count': 0,
            'pending_count': 0,
        }
    return render(request, 'bookings/my_list.html', context)


@login_required(login_url='frontend:login')
def booking_return(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, customer=request.user)
    if request.method == 'POST':
        booking.status = 'completed'
        booking.save(update_fields=['status'])
        sync_vehicle_status_after_booking_change(booking.vehicle)
        messages.success(request, "Trả xe thành công!")
        return redirect('frontend:order_list')

    today = datetime.now().date()
    late_days = max(0, (today - booking.end_date).days)
    is_late = late_days > 0
    late_hours = late_days * 24
    late_fee = Decimal(late_days) * booking.vehicle.price_per_day if is_late else Decimal("0.00")
    tax = (late_fee * Decimal("0.10")).quantize(Decimal("0.01"))
    final_total = booking.total_price + late_fee + tax

    return render(request, 'bookings/return.html', {
        'booking': booking,
        'is_late': is_late,
        'late_hours': late_hours,
        'late_fee': late_fee,
        'tax': tax,
        'final_total': final_total,
    })


@login_required(login_url='frontend:login')
def review_form(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, customer=request.user)
    existing_review = Review.objects.filter(user=request.user, vehicle=booking.vehicle).first()
    if existing_review:
        messages.info(request, "Bạn đã đánh giá xe này rồi!")
        return redirect('frontend:order_list')

    if booking.status != 'completed':
        messages.error(request, "Chỉ có thể đánh giá sau khi hoàn thành chuyến đi!")
        return redirect('frontend:order_list')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.vehicle = booking.vehicle
            review.save()
            messages.success(request, "Cảm ơn bạn đã gửi đánh giá!")
            return redirect('frontend:order_list')
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin đánh giá.")
    else:
        form = ReviewForm()
    return render(request, 'reviews/form.html', {'booking': booking, 'form': form})


# ==========================================
# 3. ADMIN OPERATIONS (DÀNH CHO QUẢN TRỊ)
# ==========================================

@user_passes_test(is_admin, login_url='frontend:login')
def admin_dashboard(request):
    total_rev = Booking.objects.filter(status='completed').aggregate(Sum('total_price'))['total_price__sum'] or 0
    new_bookings = Booking.objects.filter(status='pending').count()
    active_rentals = Booking.objects.filter(status='approved').count()
    recent_activities = Booking.objects.select_related('customer', 'vehicle').order_by('-created_at')[:10]
    vehicles = Vehicle.objects.all()

    context = {
        'total_revenue': total_rev,
        'new_bookings_count': new_bookings,
        'active_vehicles_count': active_rentals,
        'recent_activities': recent_activities,
        'vehicles': vehicles,
    }
    return render(request, 'admin/dashboard.html', context)


@user_passes_test(is_admin)
def admin_vehicle_list(request):
    vehicles = Vehicle.objects.all().order_by('-id')
    return render(request, 'admin/vehicles.html', {'vehicles': vehicles})


@user_passes_test(is_admin)
def admin_vehicle_create(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES)
        if form.is_valid():
            vehicle = form.save()
            messages.success(request, f"Đã thêm xe {vehicle.name} thành công!")
            return redirect('frontend:admin_vehicles')
        else:
            messages.error(request, "Vui lòng kiểm tra lại các trường dữ liệu nhập vào.")
    else:
        form = VehicleForm()
    return render(request, 'admin/vehicle_form.html', {'form': form, 'title': 'Thêm xe mới'})


@user_passes_test(is_admin)
def admin_vehicle_edit(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, f"Đã cập nhật thông tin xe {vehicle.name} thành công!")
            return redirect('frontend:admin_vehicles')
    else:
        form = VehicleForm(instance=vehicle)

    return render(request, 'admin/vehicle_form.html', {
        'form': form,
        'title': f'Chỉnh sửa: {vehicle.name}',
        'vehicle': vehicle
    })


@user_passes_test(is_admin)
def admin_vehicle_delete(request, vehicle_id):
    if request.method == 'POST':
        try:
            vehicle = get_object_or_404(Vehicle, id=vehicle_id)
            vehicle_name = vehicle.name
            vehicle.delete()
            return JsonResponse({'status': 'success', 'message': f'Đã xóa xe {vehicle_name}!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Yêu cầu không hợp lệ'}, status=405)


@user_passes_test(is_admin)
def admin_booking_list(request):
    bookings = Booking.objects.select_related('customer', 'vehicle').order_by('-created_at')
    return render(request, 'admin/bookings.html', {'bookings': bookings})


@user_passes_test(is_admin)
def admin_stats(request):
    total_completed = Booking.objects.filter(status='completed').count()
    total_cancelled = Booking.objects.filter(status='cancelled').count()
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    # 1. Doanh thu thực tế theo tháng
    monthly_revenue_data = Booking.objects.filter(
        status='completed', start_date__year=current_year
    ).annotate(month=ExtractMonth('start_date')).values('month').annotate(
        total=Sum('total_price')
    ).order_by('month')

    revenue_list = [0.0] * 12
    for entry in monthly_revenue_data:
        revenue_list[entry['month'] - 1] = float(entry['total'] or 0)

    # 2. Dự báo doanh thu thời gian thực (OLS Trend Projection)
    forecast_data = forecast_monthly_revenue(revenue_list, current_month)

    # 3. Tần suất thuê xe theo tháng (tính tất cả đơn không bị hủy)
    monthly_freq_data = Booking.objects.filter(
        start_date__year=current_year
    ).exclude(status='cancelled').annotate(
        month=ExtractMonth('start_date')
    ).values('month').annotate(count=Count('id')).order_by('month')

    monthly_rental_counts = [0] * 12
    for entry in monthly_freq_data:
        monthly_rental_counts[entry['month'] - 1] = entry['count']

    # 4. Tần suất thuê theo loại xe
    type_freq_qs = Booking.objects.exclude(status='cancelled').values(
        'vehicle__vehicle_type'
    ).annotate(count=Count('id'))
    type_counts_map = {row['vehicle__vehicle_type']: row['count'] for row in type_freq_qs}

    vehicle_type_labels = [label for _, label in Vehicle.VEHICLE_TYPE_CHOICES]
    vehicle_type_counts = [type_counts_map.get(code, 0) for code, _ in Vehicle.VEHICLE_TYPE_CHOICES]

    # 5. Tỷ lệ lấp đầy đội xe thời gian thực
    fleet_occupancy_percent = round(float(get_fleet_occupancy_rate() * 100), 1)

    context = {
        'total_completed': total_completed,
        'total_cancelled': total_cancelled,
        'revenue_list': revenue_list,
        'forecast_series': forecast_data['forecast_series'],
        'next_month_forecast': forecast_data['next_month_forecast'],
        'projected_annual_revenue': forecast_data['projected_annual_revenue'],
        'trend_direction': forecast_data['trend_direction'],
        'monthly_rental_counts': monthly_rental_counts,
        'vehicle_type_labels': vehicle_type_labels,
        'vehicle_type_counts': vehicle_type_counts,
        'fleet_occupancy_percent': fleet_occupancy_percent,
    }
    return render(request, 'admin/analytics.html', context)


# --- TÁC VỤ QUẢN TRỊ NHANH ---

@user_passes_test(is_admin)
def approve_order(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    booking.status = 'approved'
    booking.save(update_fields=['status'])

    booking.vehicle.status = Vehicle.STATUS_IN_USE
    booking.vehicle.save(update_fields=['status'])

    messages.success(request, f"Đã phê duyệt đơn hàng cho xe {booking.vehicle.name}")
    return redirect('frontend:admin_dashboard')


@user_passes_test(is_admin)
def admin_release_vehicle(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    vehicle.status = Vehicle.STATUS_AVAILABLE
    vehicle.save(update_fields=['status'])
    messages.success(request, f"Đã mở trạng thái cho xe {vehicle.name} thành 'Available'.")
    return redirect('frontend:admin_vehicles')


@user_passes_test(is_admin)
def update_vehicle_location(request):
    if request.method == 'POST':
        v_id = request.POST.get('vehicle_id')
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        vehicle = get_object_or_404(Vehicle, id=v_id)
        vehicle.latitude = float(lat)
        vehicle.longitude = float(lng)
        vehicle.save(update_fields=['latitude', 'longitude'])
        messages.success(request, f"Đã cập nhật tọa độ cho xe {vehicle.name}")
    return redirect('frontend:admin_dashboard')


# ==========================================
# 4. AUTH VIEWS (ĐĂNG NHẬP / ĐĂNG KÝ)
# ==========================================

def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_staff:
                messages.success(request, f"Chào mừng Admin {user.username}!")
                return redirect('frontend:admin_dashboard')
            else:
                return redirect('frontend:home')
        else:
            messages.error(request, "Tên đăng nhập hoặc mật khẩu không đúng.")
    else:
        form = UserLoginForm()
    return render(request, 'auth/login.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.save()
                messages.success(request, "Đăng ký thành công! Vui lòng đăng nhập.")
                return redirect('frontend:login')
            except Exception as e:
                messages.error(request, f"Lỗi đăng ký: {e}")
    else:
        form = RegistrationForm()
    return render(request, 'auth/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('frontend:home')
