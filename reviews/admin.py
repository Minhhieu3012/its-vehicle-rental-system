from django.contrib import admin
from .models import Review

# Register your models here.
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer',
        'vehicle',
        'booking',
        'rating',
        'comment',
        'created_at',
    )

    # list_filter = ('status', 'vehicle_type')
    # search_fields = ('name', 'license_plate')