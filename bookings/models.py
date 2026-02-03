from django.db import models
from users.models import User
from vehicles.models import Vehicle
from django.db.models.signals import post_save
from django.dispatch import receiver

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    start_date = models.DateField()
    end_date = models.DateField()

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking #{self.id} - {self.customer.username}"

# ============================================================
# LOGIC ĐỒNG BỘ ITS: Tự động đổi trạng thái xe khi duyệt đơn
# ============================================================
@receiver(post_save, sender=Booking)
def sync_vehicle_status_with_map(sender, instance, **kwargs):
    """
    Tự động cập nhật trạng thái của Vehicle dựa trên trạng thái của Booking.
    Giúp Module Bản đồ của Hiếu hiển thị đúng màu sắc Marker theo thời gian thực.
    """
    # 1. Khi Quản trị viên duyệt đơn (Approved):
    # Xe chuyển sang 'In Use' -> Hiếu sẽ hiện Marker màu đỏ trên bản đồ.
    if instance.status == 'approved':
        instance.vehicle.status = 'In Use'
        instance.vehicle.save()
        
    # 2. Khi đơn hàng hoàn thành (Completed):
    # Xe chuyển về 'Available' -> Hiếu sẽ hiện Marker màu xanh (sẵn sàng thuê).
    elif instance.status == 'completed':
        instance.vehicle.status = 'Available'
        instance.vehicle.save()
        
    # 3. Khi đơn hàng bị hủy (Cancelled):
    # Đảm bảo giải phóng xe về trạng thái sẵn sàng.
    elif instance.status == 'cancelled':
        instance.vehicle.status = 'Available'
        instance.vehicle.save()