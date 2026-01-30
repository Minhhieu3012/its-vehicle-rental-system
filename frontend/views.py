import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages

# Import Models từ các App chức năng
from vehicles.models import Vehicle
from bookings.models import Booking
from .forms import RegisterForm

def home_view(request):
    """
    Hiển thị Trang chủ: 
    - Lấy 4 xe mới nhất có ảnh để hiển thị ở Section 'Xe phổ biến'.
    """
    latest_vehicles = Vehicle.objects.exclude(image='').order_by('-created_at')[:4]
    return render(request, 'frontend/pages/home.html', {'vehicles': latest_vehicles})

def vehicle_list_view(request):
    """
    Trang danh sách xe:
    - Hiển thị toàn bộ xe cho Grid view.
    - Chuyển đổi tọa độ xe sang JSON để Leaflet Map (ITS) có thể render Marker.
    """
    vehicles_qs = Vehicle.objects.all()
    
    # Chuẩn bị dữ liệu JSON cho bản đồ
    vehicles_list = []
    for v in vehicles_qs:
        if v.latitude and v.longitude:
            vehicles_list.append({
                'id': v.id,
                'name': v.name,
                'lat': float(v.latitude),
                'lng': float(v.longitude),
                'price': float(v.price_per_day),
                'status': v.status
            })

    context = {
        'vehicles': vehicles_qs,
        'vehicles_json': json.dumps(vehicles_list)
    }
    return render(request, 'frontend/pages/vehicle_list.html', context)

def vehicle_detail_view(request, pk):
    """Trang chi tiết xe dựa trên ID (Primary Key)"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    return render(request, 'frontend/pages/vehicle_detail.html', {'vehicle': vehicle})

def payment_view(request, vehicle_id):
    """Màn hình Thanh toán (Secure Payment)"""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    # Giả lập tính tổng tiền (Ví dụ: cộng thêm phí bảo hiểm/dịch vụ 5.0)
    total_price = float(vehicle.price_per_day) + 5.00
    
    context = {
        'vehicle': vehicle,
        'total_price': total_price
    }
    return render(request, 'frontend/pages/payment.html', context)

def create_booking_view(request, vehicle_id):
    """Xử lý logic đặt xe từ Form ở trang chi tiết"""
    if request.method == 'POST':
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        Booking.objects.create(
            user=request.user,
            vehicle=vehicle,
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            total_price=vehicle.price_per_day,
            status='pending'
        )
        messages.success(request, "Giao dịch thành công! Đang chờ duyệt.")
        return redirect('home')
    return redirect('home')

def register_view(request):
    """Xử lý Đăng ký người dùng mới"""
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            messages.success(request, "Chào mừng bạn đến với XeRental!")
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'frontend/pages/register.html', {'form': form})