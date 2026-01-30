from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from .forms import RegisterForm
from vehicles.models import Vehicle
from bookings.models import Booking
import json

def home_view(request):
    """Hiển thị bản đồ ITS và 4 xe mới nhất"""
    latest_vehicles = Vehicle.objects.exclude(image='').order_by('-created_at')[:4]
    return render(request, 'frontend/pages/home.html', {'vehicles': latest_vehicles})

def payment_view(request, vehicle_id):
    """Màn hình Secure Payment"""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    context = {
        'vehicle': vehicle,
        'total_price': float(vehicle.price_per_day) + 5.00 # Ép kiểu float để tránh lỗi cộng
    }
    return render(request, 'frontend/pages/payment.html', context)

def vehicle_list_view(request):
    """Tích hợp toàn bộ xe và nạp dữ liệu JSON cho Marker bản đồ"""
    vehicles_qs = Vehicle.objects.all()
    
    vehicles_list = []
    for v in vehicles_qs:
        # Chỉ lấy xe có tọa độ để tránh lỗi bản đồ
        if v.latitude and v.longitude:
            vehicles_list.append({
                'id': v.id,
                'name': v.name,
                'lat': float(v.latitude), # Lấy từ DB
                'lng': float(v.longitude), # Lấy từ DB
                'price': float(v.price_per_day),
                'status': v.status
            })

    context = {
        'vehicles': vehicles_qs,
        'vehicles_json': json.dumps(vehicles_list)
    }
    return render(request, 'frontend/pages/vehicle_list.html', context)

def register_view(request):
    """Xử lý đăng ký"""
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
    vehicle = get_object_or_404(Vehicle, pk=pk)
    return render(request, 'frontend/pages/vehicle_detail.html', {'vehicle': vehicle})

def create_booking_view(request, vehicle_id):
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
        return redirect('frontend:home')
    return redirect('frontend:home')