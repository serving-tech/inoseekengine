from django.db import models
from parking_lots.models import ParkingSpace

class Alert(models.Model):
    parking_space = models.ForeignKey(ParkingSpace, on_delete=models.SET_NULL, null=True)
    number_plate = models.CharField(max_length=20)
    description = models.TextField()
    status = models.CharField(max_length=20, default='unresolved')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert: {self.number_plate}"