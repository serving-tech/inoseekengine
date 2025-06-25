from rest_framework import serializers
from users.models import User
from cars.models import Car
from parking_lots.models import ParkingLot, ParkingSpace
from parking_transactions.models import ParkingTransaction
from alerts.models import Alert

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone_number', 'balance', 'is_email_verified', 'created_at']

class CarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = ['id', 'user', 'number_plate', 'make', 'model', 'is_active']

class ParkingLotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingLot
        fields = '__all__'

class ParkingSpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingSpace
        fields = '__all__'

class ParkingTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingTransaction
        fields = ['id', 'car', 'parking_space', 'entry_time', 'exit_time', 'duration', 'fee', 'status']

class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = ['id', 'parking_space', 'number_plate', 'description', 'status', 'created_at']
