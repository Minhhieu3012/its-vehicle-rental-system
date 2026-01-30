from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.home, name='home'),
    
    # ĐÃ SỬA: Đổi 'vehicles/' thành 'thue-xe/' để tránh xung đột với Backend
    path('thue-xe/', views.vehicle_list, name='vehicle_list'),
    
    # URL chi tiết & thanh toán
    path('thue-xe/<int:vehicle_id>/payment/', views.vehicle_payment, name='vehicle_payment'),
    path('thue-xe/<int:vehicle_id>/reviews/', views.vehicle_reviews, name='vehicle_reviews'),

    # THÊM MỚI: Định tuyến cho Login/Register/Dashboard
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('my-orders/', views.order_list, name='order_list'),
]