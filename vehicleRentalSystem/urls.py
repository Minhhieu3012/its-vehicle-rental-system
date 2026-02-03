"""
URL configuration for vehicleRentalSystem project.
FILE ĐÃ MERGE: Kết nối Admin, Map, Booking và Frontend.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # 1. Quản trị viên (Admin)
    path('admin/', admin.site.urls),
    
    # 2. App Vehicles (Bản đồ ITS & API Xe)
    path('vehicles/', include('vehicles.urls')),

    # 3. App Bookings (Đặt xe & Thanh toán)
    path('bookings/', include('bookings.urls')),

    path('', RedirectView.as_view(url='/vehicles/map/', permanent=False)),
    
    # 4. App Reviews (Đánh giá - Lấy từ nhánh Dev nếu cần endpoint riêng, thường thì include trong vehicles)
    # path('reviews/', include('reviews.urls')),



    # 5. App Frontend (Giao diện chính - Trang chủ, Login, Register)
    # QUAN TRỌNG: Để dòng này ở cuối cùng để nó bắt đường dẫn gốc ''
    path('', include('frontend.urls')),

]

# Cấu hình load ảnh (Media) khi chạy Local
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)