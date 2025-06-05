from django.db import models
from cars.models import Car
from parking_lots.models import ParkingSpace

class ParkingTransaction(models.Model):
    car = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True)
    parking_space = models.ForeignKey(ParkingSpace, on_delete=models.SET_NULL, null=True)
    entry_time = models.DateTimeField()
    exit_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cyyks_share = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    client_share = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, default='ongoing')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.car.number_plate} - {self.status}"