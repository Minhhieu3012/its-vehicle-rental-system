from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import Booking
from vehicles.models import Vehicle
from .utils import calculate_dynamic_price, is_vehicle_available
import json
from django.utils.dateparse import parse_datetime

# Tạm thời tắt CSRF để test dễ dàng bằng Postman/Frontend đơn giản
@csrf_exempt 
def create_booking(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # 1. Lấy dữ liệu từ Frontend
            user_id = data.get('user_id') # Giả sử Frontend gửi user_id
            vehicle_id = data.get('vehicle_id')
            start_str = data.get('start_time')
            end_str = data.get('end_time')
            
            # Parse thời gian
            start_time = parse_datetime(start_str)
            end_time = parse_datetime(end_str)
            
            # 2. Logic kiểm tra xe trống 
            if not is_vehicle_available(vehicle_id, start_time, end_time):
                return JsonResponse({'error': 'Xe này đã có người đặt trong khung giờ đó!'}, status=400)
            
            # 3. Logic tính giá (Dynamic Pricing) 
            vehicle = Vehicle.objects.get(id=vehicle_id)
            total_price = calculate_dynamic_price(vehicle.price_per_hour, start_time, end_time)
            
            # 4. Lưu vào Database
            user = User.objects.get(id=user_id)
            booking = Booking.objects.create(
                user=user,
                vehicle=vehicle,
                start_time=start_time,
                end_time=end_time,
                total_price=total_price,
                status='PENDING' # Mặc định chờ Admin duyệt
            )
            
            return JsonResponse({
                'message': 'Đặt xe thành công!',
                'booking_id': booking.id,
                'total_price': total_price
            }, status=201)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)