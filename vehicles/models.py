from django.db import models
from users.models import User


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