from django.db import models
from users.models import User 

# ==========================================
# 1. MODEL XE (PHƯƠNG TIỆN)
# ==========================================
class Vehicle(models.Model):
    # Đồng bộ giá trị lưu DB là 'Available' để khớp với logic hiển thị Template
    STATUS_CHOICES = [
        ('Available', 'Available'), 
        ('Booked', 'Booked'),             
        ('In Use', 'In Use'),             
        ('Maintenance', 'Maintenance'),   
    ]

    VEHICLE_TYPE_CHOICES = [
        ('bike', 'Bike'),
        ('car_4', 'Car 4 seats'),
        ('car_7', 'Car 7 seats'),
    ]

    # Thông tin cơ bản
    name = models.CharField(max_length=100)
    license_plate = models.CharField(max_length=20, unique=True)
    
    # Liên kết chủ sở hữu (User)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='vehicles',
        null=True, 
        blank=True
    )

    # Đặc tính xe
    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPE_CHOICES,
        default='bike'
    )

    # Định giá và Trạng thái
    price_per_day = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Available'
    )

    # Tọa độ thực và Hình ảnh đại diện (Phục vụ ITS và Marker Map)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    image = models.ImageField(upload_to='vehicles/', null=True, blank=True)
    
    # Mô tả chi tiết
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.license_plate}"

    def calculate_total_price(self, start_date, end_date):
        """
        Logic tính tiền linh hoạt:
        - Tính theo số ngày thuê (tối thiểu 1 ngày).
        - Dynamic Pricing: Tăng 20% đơn giá nếu thuê vào cuối tuần (Thứ 7, CN).
        """
        # 1. Tính số ngày thuê
        delta = end_date - start_date
        days = delta.days if delta.days > 0 else 1
        
        # 2. Tính giá cơ bản
        base_price = float(self.price_per_day) * days
        
        # 3. Kiểm tra ngày bắt đầu có rơi vào cuối tuần (weekday >= 5)
        is_weekend = start_date.weekday() >= 5
        
        # 4. Áp dụng phụ phí cuối tuần
        final_price = base_price * 1.2 if is_weekend else base_price
        
        return round(final_price, 2)

# ==========================================
# 2. MODEL ẢNH CHI TIẾT (ALBUM ẢNH XE)
# ==========================================
class VehicleImage(models.Model):
    vehicle = models.ForeignKey(
        Vehicle, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = models.ImageField(
        upload_to='vehicle_gallery/', 
        verbose_name="Ảnh chi tiết"
    )

    def __str__(self):
        return f"Ảnh của xe {self.vehicle.name}"