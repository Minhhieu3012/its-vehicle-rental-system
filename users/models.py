from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from vehicles.models import Vehicle

<<<<<<< HEAD
class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Chờ duyệt'),
        ('CONFIRMED', 'Đã duyệt'),
        ('COMPLETED', 'Hoàn thành'),
        ('CANCELLED', 'Đã hủy'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.id} - {self.user.username}"
=======

class User(AbstractUser):

    driver_license_image = models.ImageField(
        upload_to="driver_licenses/",
        null=True,
        blank=True
    )

    phone_number = models.CharField(
        max_length=15,
        null=True,
        blank=True
    )

    address = models.TextField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
>>>>>>> origin/db
