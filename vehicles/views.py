from django.shortcuts import render
from django.http import JsonResponse
from .models import Vehicle
import json
from django.core.serializers.json import DjangoJSONEncoder

# --- API cho Frontend/Mobile (Nếu cần dùng sau này) ---
def vehicle_list_api(request):
    vehicles = Vehicle.objects.all()
    data = []
    for v in vehicles:
        # Kiểm tra nếu xe chưa có vị trí thì bỏ qua để tránh lỗi
        if v.latitude is None or v.longitude is None:
            continue
            
        data.append({
            'id': v.id,
            'name': v.name,
            'license_plate': v.license_plate,
            'lat': float(v.latitude),
            'lng': float(v.longitude),
            'price': float(v.price_per_day), # Sửa lại đúng tên trường trong Model
            'status': v.status,
            'image_url': v.image.url if v.image else ''
        })
    return JsonResponse({'vehicles': data})

# --- View chính để render trang Bản đồ ---
def map_view(request):
    """
    Lấy dữ liệu thật từ DB và truyền sang template map.html
    """
    # 1. Chỉ lấy những xe ĐÃ CÓ TỌA ĐỘ (latitude, longitude không được null)
    vehicles = Vehicle.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    
    vehicles_list = []
    
    for v in vehicles:
        # 2. Xử lý khớp trạng thái giữa Backend (in_use) và Frontend (in operation)
        # Model dùng 'in_use', nhưng JS cần 'in operation' để hiện màu xanh dương
        status_display = v.status
        if status_display == 'in_use':
            status_display = 'in operation'
            
        vehicles_list.append({
            'id': v.id,
            'name': v.name,
            'plate': v.license_plate, # JS gọi là 'plate', Model là 'license_plate'
            'lat': float(v.latitude),
            'lng': float(v.longitude),
            'status': status_display, # Đã xử lý khớp màu
            'price': float(v.price_per_day) # Truyền thêm giá để sau này dùng
        })

    context = {
        'vehicles_json': json.dumps(vehicles_list, cls=DjangoJSONEncoder)
    }
    # Lưu ý: Tên template của bạn là map.html hay map_demo.html? 
    # Nếu file HTML bạn đang code là map_demo.html thì giữ nguyên dòng dưới.
    return render(request, 'vehicles/map.html', context)