from django.db import models
from django.utils import timezone
from users.models import User

class ParkingLot(models.Model):
    name = models.CharField(max_length=100)
    location = models.TextField()
    capacity = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ParkingTransaction(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE)
    vehicle_number = models.CharField(max_length=20)
    check_in_time = models.DateTimeField(default=timezone.now)
    check_out_time = models.DateTimeField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    mpesa_transaction_id = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.vehicle_number} - {self.payment_status}"
