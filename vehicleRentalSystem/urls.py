# vehicleRentalSystem/urls.py (File gốc)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # 1. Module Map (App Vehicles)
    path('vehicles/', include('vehicles.urls')),

    # 2. Module Giao diện chính (App Frontend)
    # QUAN TRỌNG: Dòng này sẽ nạp file frontend/urls.py của bạn vào đường dẫn gốc ''
    path('', include('frontend.urls')), 
]

# Cấu hình media/static khi debug
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)