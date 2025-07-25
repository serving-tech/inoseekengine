from rest_framework import serializers
from users.models import User
from cars.models import Car
from parking_lots.models import ParkingLot, ParkingSpace
from parking_transactions.models import ParkingTransaction
from alerts.models import Alert
from .models import SupportTicket

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone_number', 'balance', 'is_email_verified', 'created_at', 'role']
        read_only_fields = ['id', 'balance', 'is_email_verified', 'created_at', 'role']

class ParkingLotSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    class Meta:
        model = ParkingLot
        fields = ['id', 'name', 'location', 'total_spaces', 'client']
        read_only_fields = ['id', 'total_spaces', 'created_at', 'client']

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

class SupportTicketSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    class Meta:
        model = SupportTicket
        fields = ['id', 'user', 'subject', 'message', 'status', 'created_at', 'updated_at', 'assigned_to']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'assigned_to']