from django.contrib import admin

from parking_lots.models import ParkingLot, ParkingSpace

# Register your models here.
admin.site.register(ParkingLot)
admin.site.register(ParkingSpace)


