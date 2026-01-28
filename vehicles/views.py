from django.shortcuts import render
import json

# Create your views here.
def map_view(request):
    vehicles_list = [
        {
            'plate': '59A-123.45',
            'lat': 10.762622,
            'lng': 106.660172,
            'status': 'available', 
            'name': 'VinFast Lux A2.0'
        },

        {
            'plate': '51H-999.99',
            'lat': 10.776000,
            'lng': 106.701000,
            'status': 'booked', 
            'name': 'Toyota Camry'
        },

        {
            'plate': '30E-111.22',
            'lat': 10.800000,
            'lng': 106.650000,
            'status': 'maintenance', 
            'name': 'Honda City'
        }
    ]

    # Truyen du lieu sang HTML 
    context = {
        'vehicles_json': json.dumps(vehicles_list)
    }
    return render(request, 'vehicles/map_demo.html', context)