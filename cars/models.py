from django.db import models
from users.models import User

class Car(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    number_plate = models.CharField(max_length=20, unique=True)
    make = models.CharField(max_length=50, blank=True)
    model = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.number_plate