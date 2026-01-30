"""
URL configuration for vehicleRentalSystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. Đường dẫn quản trị hệ thống (Mặc định của Django)
    path('admin/', admin.site.urls),
    
    # 2. App Vehicles (Quản lý danh sách xe, chi tiết xe và bản đồ ITS)
    # App này sẽ xử lý các đường dẫn như /vehicles/ và /vehicles/1/
    path('vehicles/', include('vehicles.urls')),

    # 3. App Bookings (Xử lý logic đặt xe và lịch sử giao dịch)
    # App này xử lý các đường dẫn như /bookings/create/
    path('bookings/', include('bookings.urls')),

    # 4. App Frontend (Giao diện chính - HTML/Sass)
    # Để đường dẫn gốc '' ở đây để xử lý Trang chủ, Đăng nhập, Đăng ký
    path('', include('frontend.urls')),
]

# Cấu hình để hiển thị ảnh từ thư mục MEDIA trong môi trường phát triển (DEBUG=True)
# Rất quan trọng để hiển thị ảnh phương tiện và ảnh GPLX người dùng đã upload
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Hỗ trợ thêm static nếu cần (tùy chọn)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)