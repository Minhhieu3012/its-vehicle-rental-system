from django.contrib import admin
from .models import Vehicle
# Register your models here.
@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'license_plate',
        'vehicle_type',
        'status',
        'price_per_day',
        'latitude',
        'longitude',
        'created_at',
    )

    list_filter = ('status', 'vehicle_type')
    search_fields = ('name', 'license_plate')