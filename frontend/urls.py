from django.urls import path
from . import views

# Namespace để gọi trong template: {% url 'frontend:home' %}
app_name = 'frontend'

urlpatterns = [
    # 1. Trang chủ - Hiển thị Banner và Xe phổ biến
    path('', views.home_view, name='home'),

    # 2. Danh sách xe - Tích hợp bản đồ ITS (Leaflet)
    path('vehicles/', views.vehicle_list_view, name='vehicle_list'),

    # 3. Chi tiết xe - Hiển thị thông số và Form đặt xe
    path('vehicle/<int:pk>/', views.vehicle_detail_view, name='vehicle_detail'),

    # 4. Thanh toán - Màn hình Secure Payment (Giao diện Thành thiết kế)
    path('payment/<int:vehicle_id>/', views.payment_view, name='payment'),

    # 5. Xử lý đặt xe - Logic Backend tạo đơn hàng (Booking)
    path('booking/create/<int:vehicle_id>/', views.create_booking_view, name='create_booking'),

    # 6. Đăng ký tài khoản - Có phần upload GPLX
    path('register/', views.register_view, name='register'),
]