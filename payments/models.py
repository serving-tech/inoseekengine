from django.db import models
from users.models import User
from parking_transactions.models import ParkingTransaction

class PaymentTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    parking_transaction = models.ForeignKey(ParkingTransaction, on_delete=models.SET_NULL, null=True)
    transaction_type = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mpesa_transaction_id = models.CharField(max_length=50, unique=True, null=True)
    status = models.CharField(max_length=20)
    transaction_time = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"

class CentralTill(models.Model):
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Central Till: {self.balance}"

class ClientTill(models.Model):
    parking_lot = models.ForeignKey('parking_lots.ParkingLot', on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Client Till for {self.parking_lot.name}: {self.balance}"