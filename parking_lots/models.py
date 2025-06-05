from django.db import models

class ParkingLot(models.Model):
    name = models.CharField(max_length=100)
    location = models.TextField()
    total_spaces = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ParkingSpace(models.Model):
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE)
    space_number = models.CharField(max_length=10)
    is_occupied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('parking_lot', 'space_number')

    def __str__(self):
        return f"{self.parking_lot.name} - {self.space_number}"