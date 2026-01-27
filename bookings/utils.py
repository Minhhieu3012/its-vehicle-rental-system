from django.utils import timezone
from .models import Booking

def calculate_dynamic_price(vehicle_price, start_time, end_time):
    """
    Tính giá tiền dựa trên thời gian thuê.
    Logic: Tăng giá 20% nếu thuê vào cuối tuần (T7, CN). 
    """
    duration = end_time - start_time
    hours = duration.total_seconds() / 3600
    
    # Giá cơ bản
    base_total = float(vehicle_price) * hours
    
    # Dynamic Pricing: Kiểm tra xem ngày bắt đầu có phải cuối tuần không
    # weekday(): 0=Mon, ... 5=Sat, 6=Sun
    if start_time.weekday() >= 5: 
        final_price = base_total * 1.2 # Tăng 20%
    else:
        final_price = base_total
        
    return round(final_price, 2)

def is_vehicle_available(vehicle_id, start_time, end_time):
    """
    Kiểm tra xem xe có bị trùng lịch không. 
    Logic: Tìm các booking ĐÃ ĐƯỢC DUYỆT hoặc CHỜ DUYỆT mà khoảng thời gian bị chồng lấn.
    """
    overlapping_bookings = Booking.objects.filter(
        vehicle_id=vehicle_id,
        status__in=['PENDING', 'CONFIRMED'], # Chỉ check đơn chưa hủy
        start_time__lt=end_time, # Bắt đầu của đơn cũ < Kết thúc đơn mới
        end_time__gt=start_time  # Kết thúc của đơn cũ > Bắt đầu đơn mới
    )
    
    # Nếu có overlapping -> False (Không rảnh), ngược lại True
    return not overlapping_bookings.exists()