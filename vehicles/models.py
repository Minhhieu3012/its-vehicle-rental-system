from django.db import models
from users.models import User

<<<<<<< HEAD
class Vehicle(models.Model):
    # Định nghĩa các trạng thái xe 
    STATUS_CHOICES = [
        ('AVAILABLE', 'Sẵn sàng'),
        ('BOOKED', 'Đã đặt'),
        ('IN_USE', 'Đang đi'),
        ('MAINTENANCE', 'Bảo trì'),
    ]

    name = models.CharField(max_length=100)
    license_plate = models.CharField(max_length=20, unique=True) # Biển số
    image = models.ImageField(upload_to='vehicles/', blank=True, null=True) # 
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2) # Giá gốc
    
    # Tọa độ cho team Map (Leaflet) 
    latitude = models.FloatField(default=10.8231) # Ví dụ: Tọa độ SG
    longitude = models.FloatField(default=106.6297)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.license_plate}"
=======

class Vehicle(models.Model):

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('rented', 'Rented'),
        ('maintenance', 'Maintenance'),
    ]

    name = models.CharField(max_length=100)

    license_plate = models.CharField(
        max_length=20,
        unique=True
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vehicles'
    )

    price_per_day = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available'
    )

    description = models.TextField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.license_plate}"
>>>>>>> origin/db
