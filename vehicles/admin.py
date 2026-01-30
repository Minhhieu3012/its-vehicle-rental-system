from django.contrib import admin
from .models import Vehicle, Review, VehicleImage

# 1. Phần Upload ảnh (Lấy từ nhánh HEAD)
class VehicleImageInline(admin.TabularInline):
    model = VehicleImage
    extra = 5  # Cho phép up 5 ảnh cùng lúc

# 2. Phần Quản lý Xe (Gộp cả 2 nhánh)
@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    # Lấy danh sách hiển thị chi tiết từ nhánh Dev (để phục vụ Map)
    list_display = (
        'id',
        'name',
        'license_plate',
        'vehicle_type',
        'status',          # Quan trọng cho Map đổi màu
        'price_per_day',
        'latitude',        # Quan trọng cho Map
        'longitude',       # Quan trọng cho Map
        'created_at',
    )

    # Bộ lọc và Tìm kiếm từ nhánh Dev
    list_filter = ('status', 'vehicle_type')
    search_fields = ('name', 'license_plate')
    
    # Tích hợp thêm phần Upload ảnh từ nhánh HEAD
    inlines = [VehicleImageInline] 

# 3. Phần Đánh giá (Lấy từ nhánh HEAD)
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'vehicle', 'rating', 'created_at')
    list_filter = ('rating',)