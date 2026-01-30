from django.urls import path
from . import views

<<<<<<< HEAD
app_name = 'bookings'

urlpatterns = [
    # path('create/<int:vehicle_id>/', views.create_booking_view, name='create'),
]
=======
urlpatterns = [
    path("api/create/", views.create_booking, name="create_booking"),
    path("api/my/", views.my_bookings, name="my_bookings"),
    path("api/<int:booking_id>/cancel/", views.cancel_booking, name="cancel_booking"),
    path("api/<int:booking_id>/approve/", views.approve_booking, name="approve_booking"),
    path("api/<int:booking_id>/complete/", views.complete_booking, name="complete_booking"),
]
>>>>>>> origin/dev
