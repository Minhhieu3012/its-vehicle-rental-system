from django.db import models
from django.contrib.auth.models import User

# 1. MODEL XE (Tạo tạm )
class Vehicle(models.Model):
    name = models.CharField(max_length=200, verbose_name="Tên xe")
    price_per_day = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Giá thuê/ngày")
    image = models.ImageField(upload_to='vehicles/', blank=True, null=True, verbose_name="Ảnh xe")
    is_available = models.BooleanField(default=True, verbose_name="Sẵn sàng")

    def __str__(self):
        return self.name

class Review(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='reviews', verbose_name="Xe")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Người dùng")
    
    RATING_CHOICES = [
        (1, '1 Sao - Tệ'),
        (2, '2 Sao - Kém'),
        (3, '3 Sao - Bình thường'),
        (4, '4 Sao - Tốt'),
        (5, '5 Sao - Tuyệt vời'),
    ]
    rating = models.IntegerField(choices=RATING_CHOICES, default=5, verbose_name="Điểm đánh giá")
    comment = models.TextField(blank=True, null=True, verbose_name="Nhận xét")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    def __str__(self):
        return f"{self.user.username} đánh giá {self.vehicle.name}"

class VehicleImage(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='vehicle_gallery/', verbose_name="Ảnh chi tiết")

    def __str__(self):
        return f"Ảnh của xe {self.vehicle.name}"