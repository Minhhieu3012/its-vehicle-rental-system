from django.urls import path
from . import views

urlpatterns = [
    path('api/list/', views.vehicle_list_api, name='vehicle_list_api'),
]