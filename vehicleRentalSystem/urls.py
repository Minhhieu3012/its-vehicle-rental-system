from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # App routes
    path("bookings/", include("bookings.urls")),
    path("vehicles/", include("vehicles.urls")),
]

# Serve media when DEBUG=True (dev only)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
