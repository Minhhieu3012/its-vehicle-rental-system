from django.http import JsonResponse
from .models import Vehicle

def vehicle_list_api(request):
    """
    API trả về danh sách xe dạng JSON cho Frontend và Map 
    """
    vehicles = Vehicle.objects.all()
    data = []
    for v in vehicles:
        data.append({
            'id': v.id,
            'name': v.name,
            'license_plate': v.license_plate,
            'lat': v.latitude,
            'lng': v.longitude,
            'price': float(v.price_per_hour),
            'status': v.status,
            'image_url': v.image.url if v.image else ''
        })
    return JsonResponse({'vehicles': data})