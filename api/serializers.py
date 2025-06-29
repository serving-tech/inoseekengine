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
        read_only_fields = ['id', 'balance', 'is_email_verified', 'created_at']

class ParkingLotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingLot
        fields = ['id', 'name', 'location', 'total_spaces']
        read_only_fields = ['id', 'total_spaces', 'created_at']

class ParkingSpaceSerializer(serializers.ModelSerializer):
    parking_lot = ParkingLotSerializer(read_only=True)
    class Meta:
        model = ParkingSpace
        fields = ['id', 'parking_lot', 'space_number', 'is_occupied', 'created_at']
        read_only_fields = ['id', 'parking_lot', 'is_occupied', 'created_at']

class CarSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Car
        fields = ['id', 'user', 'number_plate', 'make', 'model', 'is_active', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class ParkingTransactionSerializer(serializers.ModelSerializer):
    car = CarSerializer(read_only=True)
    parking_space = ParkingSpaceSerializer(read_only=True)
    class Meta:
        model = ParkingTransaction
        fields = [
            'id', 'car', 'parking_space', 'entry_time', 'exit_time',
            'duration', 'fee', 'cyyks_share', 'client_share', 'status', 'created_at'
        ]
        read_only_fields = [
            'id', 'car', 'parking_space', 'entry_time', 'exit_time',
            'duration', 'fee', 'cyyks_share', 'client_share', 'status', 'created_at'
        ]

class AlertSerializer(serializers.ModelSerializer):
    parking_space = ParkingSpaceSerializer(read_only=True)
    class Meta:
        model = Alert
        fields = ['id', 'parking_space', 'number_plate', 'description', 'status', 'created_at']
        read_only_fields = ['id', 'parking_space', 'created_at', 'status']