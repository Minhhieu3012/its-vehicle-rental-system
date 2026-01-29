from django.shortcuts import render
import json

# Create your views here.
def map_view(request):
    vehicles_list = [
        {
            'id': 1,
            'plate': '59A-123.45',
            'lat': 10.762622,
            'lng': 106.660172,
            'status': 'available', 
            'name': 'VinFast Lux A2.0'
        },

        {
            'id': 2,
            'plate': '51H-999.99',
            'lat': 10.776000,
            'lng': 106.701000,
            'status': 'booked', 
            'name': 'Toyota Camry'
        },

        {
            'id': 3,
            'plate': '30E-111.22',
            'lat': 10.800000,
            'lng': 106.650000,
            'status': 'in operation', 
            'name': 'Honda City'
        },

        {
            'id': 4,
            'plate': '70F-333.44',
            'lat': 10.730000,
            'lng': 106.680000,
            'status': 'maintenance', 
            'name': 'Ford Focus'
        }
    ]

    # Truyen du lieu sang HTML 
    context = {
        'vehicles_json': json.dumps(vehicles_list)
    }
    return render(request, 'vehicles/map.html', context)