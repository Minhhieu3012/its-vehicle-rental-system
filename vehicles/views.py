from django.shortcuts import render
from django.http import JsonResponse
from .models import Vehicle
import json

# --- API cho Frontend/Mobile gọi qua Ajax ---
def vehicle_list_api(request):
    """
    API trả về danh sách xe dạng JSON lấy từ Database
    """
    vehicles = Vehicle.objects.all()
    data = []
    for v in vehicles:
        data.append({
            'id': v.id,
            'name': v.name,
            'license_plate': v.license_plate,
            'lat': float(v.latitude), # Đảm bảo là số để bản đồ đọc được
            'lng': float(v.longitude),
            'price': float(v.price_per_hour),
            'status': v.status,
            'image_url': v.image.url if v.image else ''
        })
    return JsonResponse({'vehicles': data})

# --- View để render trang Bản đồ ---
def map_view(request):
    """
    Lấy dữ liệu thật từ DB và truyền sang template map.html
    """
    vehicles = Vehicle.objects.all()
    vehicles_list = []
    
    for v in vehicles:
        vehicles_list.append({
            'id': v.id,
            'name': v.name,
            'plate': v.license_plate,
            'lat': float(v.latitude),
            'lng': float(v.longitude),
            'status': v.status,
        })

    context = {
        'vehicles_json': json.dumps(vehicles_list)
    }
    return render(request, 'vehicles/map.html', context)