"""
URL configuration for vehicleRentalSystem project.
FILE ĐÃ MERGE: Kết nối Admin, Map, Booking, Frontend và Media Static.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. Quản trị viên (Admin)
    path('admin/', admin.site.urls),
    
    # 2. App Vehicles (Bản đồ ITS & API Xe)
    path('vehicles/', include('vehicles.urls')),

    # 3. App Bookings (Đặt xe & Thanh toán)
    path('bookings/', include('bookings.urls')),
    
    # 4. App Reviews (Nếu có endpoint riêng)
    # path('reviews/', include('reviews.urls')),

    # 5. App Frontend (Giao diện chính - Trang chủ, Login, Register)
    # QUAN TRỌNG: Để dòng này ở cuối cùng để nó bắt đường dẫn gốc ''
    path('', include(('frontend.urls', 'frontend'), namespace='frontend')),
]

# Cấu hình load ảnh (Media) và file tĩnh (Static) khi chạy Local
if settings.DEBUG:
    # Cho phép truy cập ảnh xe qua URL /media/...
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Hỗ trợ load CSS/JS trong môi trường phát triển
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)