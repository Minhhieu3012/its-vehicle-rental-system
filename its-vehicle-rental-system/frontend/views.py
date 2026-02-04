from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q, Sum
from django.db.models.functions import ExtractMonth
from django.http import JsonResponse
from datetime import datetime, timedelta

# Import Forms
from .forms import (
    RegistrationForm, UserLoginForm, 
    ReviewForm, VehicleForm
)

# --- IMPORT MODELS ---
try:
    from vehicles.models import Vehicle
    from bookings.models import Booking
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:
    Vehicle = None
    Booking = None
    User = None

# Hàm kiểm tra quyền Admin chuyên sâu
def is_admin(user):
    return user.is_authenticated and user.is_staff

# ==========================================
# 1. PUBLIC VIEWS (DÀNH CHO MỌI NGƯỜI)
# ==========================================

def home(request):
    if Vehicle:
        # Lấy 8 xe mới nhất để hiển thị ở trang chủ
        vehicles = Vehicle.objects.all().order_by('-id')[:8]
    else:
        vehicles = []

    vehicle_name = request.GET.get('q')
    vehicle_type = request.GET.get('type')

    if vehicle_name and vehicles:
        vehicles = vehicles.filter(name__icontains=vehicle_name)
    if vehicle_type and vehicles: 
        vehicles = vehicles.filter(vehicle_type=vehicle_type) 

    return render(request, 'frontend/pages/home.html', {'featured_vehicles': vehicles})

def map_view(request):
    """Hàm lấy dữ liệu xe thực tế truyền vào bản đồ ITS (Đã tối ưu logic gộp)"""
    if not Vehicle:
        return render(request, 'frontend/pages/map.html', {'vehicles': [], 'vehicles_json': []})

    # Chỉ lấy những xe có tọa độ thực tế trên bản đồ
    vehicles = Vehicle.objects.exclude(Q(latitude__isnull=True) | Q(longitude__isnull=True))
    vehicles_json = []
    
    for v in vehicles:
        # Xử lý lấy tọa độ linh hoạt từ nhiều tên trường (latitude/lat)
        lat = getattr(v, 'latitude', 0) or getattr(v, 'lat', 0)
        lng = getattr(v, 'longitude', 0) or getattr(v, 'lng', 0)
        
        vehicles_json.append({
            'id': v.id,
            'name': getattr(v, 'name', 'Xe'),
            'lat': float(lat),
            'lng': float(lng),
            'status': getattr(v, 'status', 'Available'),
            'status_display': v.get_status_display() if hasattr(v, 'get_status_display') else str(v.status),
            'image_url': v.image.url if v.image else '/static/frontend/img/placeholder.jpg',
            'detail_url': reverse('frontend:vehicle_detail', args=[v.id]),
            'price': float(getattr(v, 'price_per_day', 0) or getattr(v, 'daily_rate', 0)),
            'rating': 4.8, 
            'trips': 12 
        })

    return render(request, 'frontend/pages/map.html', {
        'vehicles': vehicles, 
        'vehicles_json': vehicles_json
    })

def vehicle_list(request):
    vehicles = Vehicle.objects.all() if Vehicle else []
    sort_by = request.GET.get('sort')
    if sort_by == 'price_asc':
        vehicles = vehicles.order_by('price_per_day')
    elif sort_by == 'price_desc':
        vehicles = vehicles.order_by('-price_per_day')
    return render(request, 'frontend/vehicles/list.html', {'vehicles': vehicles})

def vehicle_detail(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    return render(request, 'frontend/vehicles/detail.html', {'vehicle': vehicle})

# ==========================================
# 2. USER OPERATIONS (DÀNH CHO NGƯỜI THUÊ)
# ==========================================

@login_required(login_url='frontend:login')
def vehicle_payment(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    
    # Lấy ngày từ POST (khi ấn từ trang Detail) hoặc GET (khi ấn từ Bản đồ)
    pickup_str = request.POST.get('pickup_date') or request.GET.get('pickup_date', '')
    return_str = request.POST.get('return_date') or request.GET.get('return_date', '')
    
    try:
        p_date = datetime.strptime(pickup_str.split(',')[0].strip(), "%Y-%m-%d").date()
        r_date = datetime.strptime(return_str.split(',')[0].strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError, IndexError, TypeError):
        # Nếu không có ngày truyền vào, mặc định thuê 1 ngày bắt đầu từ hôm nay
        p_date = datetime.now().date()
        r_date = p_date + timedelta(days=1) 

    # --- KHẮC PHỤC LỖI: Gọi hàm tính toán đã gộp phụ phí 20% cuối tuần ---
    if hasattr(vehicle, 'calculate_total_price'):
        total_price = vehicle.calculate_total_price(p_date, r_date)
    else:
        # Logic dự phòng nếu Model chưa kịp đồng bộ
        delta = r_date - p_date
        days = delta.days if delta.days > 0 else 1
        total_price = vehicle.price_per_day * days

    delta = r_date - p_date
    days = delta.days if delta.days > 0 else 1

    if request.method == 'POST' and 'payment_method' in request.POST:
        try:
            Booking.objects.create(
                customer=request.user,
                vehicle=vehicle,
                start_date=p_date,
                end_date=r_date,
                total_price=total_price,
                status='pending'
            )
            # Tự động cập nhật xe sang trạng thái Booked khi khách đặt
            vehicle.status = 'Booked'
            vehicle.save()
            messages.success(request, "Thanh toán thành công! Đơn hàng đang chờ xác nhận.")
            return redirect('/my-orders/') 
        except Exception as e:
            messages.error(request, f"Lỗi hệ thống: {str(e)}")
            return redirect(f'/thue-xe/{vehicle_id}/')

    return render(request, 'frontend/bookings/payment.html', {
        'vehicle': vehicle, 'pickup_date': p_date, 'return_date': r_date,
        'days': days, 'total_price': total_price, 'is_weekend': p_date.weekday() >= 5
    })

@login_required(login_url='frontend:login')
def order_list(request):
    if not Booking:
        return render(request, 'frontend/bookings/my_list.html', {'bookings': []})
    try:
        bookings_qs = Booking.objects.filter(customer=request.user).order_by('-id')
        status_filter = request.GET.get('status')
        search_query = request.GET.get('q')

        if status_filter and status_filter != 'all':
            bookings_qs = bookings_qs.filter(status=status_filter)
        if search_query:
            bookings_qs = bookings_qs.filter(Q(vehicle__name__icontains=search_query) | Q(vehicle__license_plate__icontains=search_query))

        all_user_bookings = Booking.objects.filter(customer=request.user)
        context = {
            'bookings': bookings_qs,
            'active_count': all_user_bookings.filter(status='approved').count(),
            'completed_count': all_user_bookings.filter(status='completed').count(),
            'pending_count': all_user_bookings.filter(status='pending').count(),
        }
    except Exception as e:
        messages.error(request, f"Lỗi hiển thị danh sách: {str(e)}")
        context = {'bookings': [], 'active_count': 0, 'completed_count': 0, 'pending_count': 0}
    return render(request, 'frontend/bookings/my_list.html', context)

@login_required(login_url='frontend:login')
def booking_return(request, booking_id):
    """Xử lý khách hàng trả xe: ĐỒNG BỘ Cập nhật trạng thái về 'Available' chuẩn xác"""
    booking = get_object_or_404(Booking, pk=booking_id, customer=request.user)
    if request.method == 'POST':
        booking.status = 'completed'
        # Cập nhật trạng thái xe về chuẩn 'Available'
        booking.vehicle.status = 'Available' 
        booking.vehicle.save()
        booking.save()
        messages.success(request, "Trả xe thành công!")
        return redirect('/my-orders/')
    return render(request, 'frontend/bookings/return.html', {'booking': booking})

@login_required(login_url='frontend:login')
def review_form(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, customer=request.user)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.user = request.user
            review.vehicle = booking.vehicle
            review.save()
            messages.success(request, "Cảm ơn bạn đã gửi đánh giá!")
            return redirect('/my-orders/')
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin đánh giá.")
    else:
        form = ReviewForm()
    return render(request, 'frontend/reviews/form.html', {'booking': booking, 'form': form})

# ==========================================
# 3. ADMIN OPERATIONS (DÀNH CHO QUẢN TRỊ)
# ==========================================

@user_passes_test(is_admin, login_url='frontend:login')
def admin_dashboard(request):
    """Trang tổng quan quản trị với dữ liệu thật"""
    total_rev = Booking.objects.filter(status='completed').aggregate(Sum('total_price'))['total_price__sum'] or 0
    new_bookings = Booking.objects.filter(status='pending').count()
    active_rentals = Booking.objects.filter(status='approved').count()
    recent_activities = Booking.objects.all().order_by('-created_at')[:10]
    vehicles = Vehicle.objects.all()

    context = {
        'total_revenue': total_rev,
        'new_bookings_count': new_bookings,
        'active_vehicles_count': active_rentals,
        'recent_activities': recent_activities,
        'vehicles': vehicles,
    }
    return render(request, 'frontend/admin/dashboard.html', context)

@user_passes_test(is_admin)
def admin_vehicle_list(request):
    """Quản lý danh sách xe chi tiết cho Admin"""
    vehicles = Vehicle.objects.all().order_by('-id')
    return render(request, 'frontend/admin/vehicles.html', {'vehicles': vehicles})

@user_passes_test(is_admin)
def admin_vehicle_create(request):
    """Thêm xe mới và điều hướng chuẩn xác về danh sách Admin"""
    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES)
        if form.is_valid():
            vehicle = form.save() 
            messages.success(request, f"Đã thêm xe {vehicle.name} vào hệ thống thành công!")
            return redirect('frontend:admin_vehicles')
        else:
            messages.error(request, "Vui lòng kiểm tra lại các trường dữ liệu nhập vào.")
    else:
        form = VehicleForm()
    return render(request, 'frontend/admin/vehicle_form.html', {'form': form, 'title': 'Thêm xe mới'})

@user_passes_test(is_admin)
def admin_booking_list(request):
    """Danh sách tất cả đơn hàng cho Admin"""
    bookings = Booking.objects.all().order_by('-created_at')
    return render(request, 'frontend/admin/bookings.html', {'bookings': bookings})

@user_passes_test(is_admin)
def admin_stats(request):
    """Trang thống kê hệ thống với biểu đồ doanh thu theo tháng"""
    total_completed = Booking.objects.filter(status='completed').count()
    total_cancelled = Booking.objects.filter(status='cancelled').count()
    current_year = datetime.now().year
    monthly_revenue_data = Booking.objects.filter(
        status='completed', start_date__year=current_year
    ).annotate(month=ExtractMonth('start_date')).values('month').annotate(total=Sum('total_price')).order_by('month')

    revenue_list = [0] * 12
    for entry in monthly_revenue_data:
        revenue_list[entry['month'] - 1] = float(entry['total'])

    context = {
        'total_completed': total_completed,
        'total_cancelled': total_cancelled,
        'revenue_list': revenue_list,
    }
    return render(request, 'frontend/admin/analytics.html', context)

# --- TÁC VỤ QUẢN TRỊ NHANH ---

@user_passes_test(is_admin)
def approve_order(request, booking_id):
    """Admin phê duyệt đơn: Cập nhật trạng thái Booking và trạng thái Xe"""
    booking = get_object_or_404(Booking, id=booking_id)
    booking.status = 'approved'
    booking.vehicle.status = 'Booked' # Đồng bộ chuỗi 'Booked'
    booking.vehicle.save()
    booking.save() 
    messages.success(request, f"Đã phê duyệt đơn hàng cho xe {booking.vehicle.name}")
    return redirect('frontend:admin_dashboard')

@user_passes_test(is_admin)
def admin_release_vehicle(request, vehicle_id):
    """Admin mở trạng thái xe thủ công về 'Available'"""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    vehicle.status = 'Available' # Đồng bộ chuỗi chuẩn 'Available'
    vehicle.save()
    messages.success(request, f"Đã mở trạng thái cho xe {vehicle.name} thành 'Có sẵn'.")
    return redirect('frontend:admin_vehicles')

@user_passes_test(is_admin)
def update_vehicle_location(request):
    """Cập nhật tọa độ xe từ giao diện Admin"""
    if request.method == 'POST':
        v_id = request.POST.get('vehicle_id')
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        vehicle = get_object_or_404(Vehicle, id=v_id)
        vehicle.latitude = float(lat)
        vehicle.longitude = float(lng)
        vehicle.save() 
        messages.success(request, f"Đã cập nhật tọa độ cho xe {vehicle.name}")
    return redirect('frontend:admin_dashboard')

# ==========================================
# 4. AUTH VIEWS (ĐĂNG NHẬP / ĐĂNG KÝ)
# ==========================================

def login_view(request):
    """Xử lý đăng nhập phân quyền: Admin vào Dashboard, User vào Home"""
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Kiểm tra quyền Staff để điều hướng tách biệt
            if user.is_staff:
                messages.success(request, f"Chào mừng Admin {user.username} quay trở lại!")
                return redirect('frontend:admin_dashboard')
            else:
                return redirect('frontend:home')
        else:
            messages.error(request, "Tên đăng nhập hoặc mật khẩu không đúng.")
    else:
        form = UserLoginForm()
    return render(request, 'frontend/auth/login.html', {'form': form})

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
    return render(request, 'frontend/auth/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('frontend:home')