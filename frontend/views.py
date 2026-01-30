from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from .forms import RegisterForm
from vehicles.models import Vehicle
from bookings.models import Booking
import json

def home_view(request):
    """Hiển thị bản đồ ITS và 4 xe mới nhất của Bảo"""
    latest_vehicles = Vehicle.objects.all().order_by('-created_at')[:4]
    return render(request, 'frontend/pages/home.html', {'vehicles': latest_vehicles})

def payment_view(request, vehicle_id):
    """Màn hình Secure Payment - Tóm tắt chuyến đi và Form thanh toán"""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    # Logic tính toán sơ bộ (giả định thuê 1 ngày)
    context = {
        'vehicle': vehicle,
        'total_price': vehicle.price_per_day + 5.00 # Giá xe + phí dịch vụ
    }
    return render(request, 'frontend/pages/payment.html', context)

def vehicle_list_view(request):
    """Tích hợp toàn bộ xe và nạp dữ liệu JSON cho Marker bản đồ của Hiếu"""
    vehicles_qs = Vehicle.objects.all()
    # Chuyển đổi dữ liệu sang JSON để Javascript của Leaflet có thể đọc
    vehicles_list = [{
        'id': v.id,
        'name': v.name,
        'lat': 10.762622, # Tọa độ mặc định dự án (có thể lấy từ model nếu Hiếu đã thêm field)
        'lng': 106.660172,
        'price': float(v.price_per_day)
    } for v in vehicles_qs]

    context = {
        'vehicles': vehicles_qs,
        'vehicles_json': json.dumps(vehicles_list)
    }
    return render(request, 'frontend/pages/vehicle_list.html', context)

def register_view(request):
    """Xử lý đăng ký tài khoản và GPLX"""
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            messages.success(request, "Chào mừng bạn đến với DriveEase!")
            return redirect('frontend:home')
    else:
        form = RegisterForm()
    return render(request, 'frontend/pages/register.html', {'form': form})

def vehicle_detail_view(request, pk):
    """Chi tiết xe của Bảo"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    return render(request, 'frontend/pages/vehicle_detail.html', {'vehicle': vehicle})

def create_booking_view(request, vehicle_id):
    """Xác nhận thanh toán và lưu vào DB Bookings"""
    if request.method == 'POST':
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        Booking.objects.create(
            user=request.user,
            vehicle=vehicle,
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            total_price=vehicle.price_per_day,
            status='pending' # Chờ Admin duyệt
        )
        messages.success(request, "Giao dịch thành công! Yêu cầu của bạn đang được xét duyệt.")
        return redirect('frontend:home')