from django.db import models
from users.models import User


class Vehicle(models.Model):

    STATUS_CHOICES = [
        ('available', 'Available'),       # Xe sẵn sàng
        ('booked', 'Booked'),             # Đã đặt, chưa nhận
        ('in_use', 'In Use'),              # Đang sử dụng
        ('maintenance', 'Maintenance'),   # Bảo trì
    ]

    VEHICLE_TYPE_CHOICES = [
        ('bike', 'Bike'),
        ('car_4', 'Car 4 seats'),
        ('car_7', 'Car 7 seats'),
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

    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPE_CHOICES,
        default='bike'
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

    latitude = models.FloatField(
        null=True,
        blank=True
    )

    longitude = models.FloatField(
        null=True,
        blank=True
    )


    image = models.ImageField(
        upload_to='vehicles/',
        null=True,
        blank=True
    )

    description = models.TextField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.license_plate}"
