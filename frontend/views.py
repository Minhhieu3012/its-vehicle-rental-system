from django.shortcuts import render, get_object_or_404, redirect
from vehicles.models import Vehicle 

def home(request):
    # Lấy xe mới nhất
    vehicles = Vehicle.objects.all().order_by('-created_at')[:8] 

    # Logic tìm kiếm cơ bản
    vehicle_name = request.GET.get('q')
    vehicle_type = request.GET.get('type')

    if vehicle_name:
        vehicles = Vehicle.objects.filter(name__icontains=vehicle_name)
    if vehicle_type:
        vehicles = vehicles.filter(seats=vehicle_type)

    return render(request, 'frontend/pages/home.html', {'vehicles': vehicles})

def vehicle_list(request):
    # SỬA LỖI: Tên file template phải khớp với file thực tế
    vehicles = Vehicle.objects.all()
    # Lưu ý: File template của bạn tên là 'vehicles_list.html' (có s) hay không có s?
    # Tôi sẽ chuẩn hóa về 'vehicle_list.html' (số ít) cho đúng chuẩn Django
    return render(request, 'frontend/pages/vehicle_list.html', {'vehicles': vehicles})

def vehicle_payment(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    
    # Giả lập logic tính tiền (sau này lấy từ form ngày tháng)
    days = 3 
    total = vehicle.price_per_day * days
    
    context = {
        'vehicle': vehicle,
        'rental_info': {
            'days': days,
            'total_amount': total,
            'service_fee': total * 0.1, # Ví dụ phí dịch vụ 10%
            'final_total': total * 1.1
        }
    }
    return render(request, 'frontend/pages/payment.html', context)

def vehicle_reviews(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    return render(request, 'frontend/pages/review.html', {'vehicle': vehicle})

# --- CÁC VIEW MỚI BỔ SUNG CHO ĐỦ HỆ THỐNG ---
def login_view(request):
    return render(request, 'frontend/pages/login.html')

def register_view(request):
    return render(request, 'frontend/pages/register.html')

def order_list(request):
    return render(request, 'frontend/pages/order_list.html')