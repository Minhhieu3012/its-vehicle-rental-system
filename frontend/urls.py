from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('vehicles/', views.vehicle_list_view, name='vehicle_list'),
    path('vehicle/<int:pk>/', views.vehicle_detail_view, name='vehicle_detail'),
    # Route dẫn đến màn hình Secure Payment của Thành
    path('payment/<int:vehicle_id>/', views.payment_view, name='payment'),
    path('booking/create/<int:vehicle_id>/', views.create_booking_view, name='create_booking'),
]