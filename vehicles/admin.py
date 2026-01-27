from django.contrib import admin
from .models import Vehicle, Review, VehicleImage

class VehicleImageInline(admin.TabularInline):
    model = VehicleImage
    extra = 5  

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_per_day', 'is_available')
    search_fields = ('name',)
    
    inlines = [VehicleImageInline] 

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'vehicle', 'rating', 'created_at')
    list_filter = ('rating',)