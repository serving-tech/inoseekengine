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
        fields = [
            'id', 'name', 'email', 'phone_number',
            'balance', 'is_email_verified', 'created_at', 'role'
        ]
        read_only_fields = ['id', 'balance', 'is_email_verified', 'created_at', 'role']



# class UserSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(
#         write_only=True,
#         required=False,
#         min_length=8,
#         help_text="Password must be at least 8 characters long"
#     )
#
#     class Meta:
#         model = User
#         fields = [
#             'id', 'name', 'email', 'phone_number',
#             'balance', 'is_email_verified', 'created_at', 'role', 'password'
#         ]
#         read_only_fields = ['id', 'balance', 'is_email_verified', 'created_at', 'role']
#
#     def create(self, validated_data):
#         password = validated_data.pop('password', None)
#         role = validated_data.pop('role', 'driver')  # get provided role or default
#         user = User(**validated_data)
#         user.role = role  # <-- respects incoming role
#         if password:
#             user.set_password(password)
#         else:
#             user.set_unusable_password()
#         user.save()
#         return user
#
#
#     def update(self, instance, validated_data):
#         # Ensure only company_admin can update users
#         request = self.context.get('request')
#         if not request or not request.user.is_authenticated:
#             raise serializers.ValidationError({"detail": "Authentication required."})
#         if request.user.role != 'company_admin':
#             raise serializers.ValidationError({"detail": "Only company admin users can update clients or users."})
#
#         password = validated_data.pop('password', None)
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         if password:
#             instance.set_password(password)
#         instance.save()
#         return instance


# class ParkingLotSerializer(serializers.ModelSerializer):
#     client = UserSerializer(read_only=True)

#     class Meta:
#         model = ParkingLot
#         fields = ['id', 'name', 'location', 'total_spaces', 'client', 'created_at']
#         read_only_fields = ['id', 'created_at', 'client']


class ParkingLotSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)      # Nested client data for display
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='client'),
        source='client',
        write_only=True
    )

    class Meta:
        model = ParkingLot
        fields = [
            'id',
            'name',
            'location',
            'total_spaces',
            'client',       # Read-only nested data
            'client_id',    # For POST/PUT
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

class ParkingSpaceSerializer(serializers.ModelSerializer):
    parking_lot = ParkingLotSerializer(read_only=True)

    class Meta:
        model = ParkingSpace
        fields = ['id', 'parking_lot', 'space_number', 'is_occupied', 'created_at']
        read_only_fields = ['id', 'parking_lot', 'is_occupied', 'created_at']


class CarSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Keep user as read-only for serialization output

    class Meta:
        model = Car
        fields = ['id', 'user', 'number_plate', 'make', 'model', 'is_active', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def create(self, validated_data):
        # Set the user from the request context
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class ParkingTransactionSerializer(serializers.ModelSerializer):
    car = CarSerializer(read_only=True)
    parking_space = ParkingSpaceSerializer(read_only=True)

    # New computed fields
    name = serializers.SerializerMethodField()
    location_name = serializers.SerializerMethodField()

    class Meta:
        model = ParkingTransaction
        fields = [
            'id', 'car', 'parking_space',
            'entry_time', 'exit_time', 'duration', 'fee',
            'cyyks_share', 'client_share', 'status', 'created_at',
            'name',           # NEW
            'location_name'   # NEW
        ]
        read_only_fields = [
            'id', 'car', 'parking_space', 'entry_time', 'exit_time',
            'duration', 'fee', 'cyyks_share', 'client_share',
            'status', 'created_at', 'name', 'location_name'
        ]

    def get_name(self, obj):
        """Get driver's name from linked car user"""
        if obj.car and obj.car.user:
            return obj.car.user.name or obj.car.user.email
        return "N/A"

    def get_location_name(self, obj):
        """Get parking lot name from linked parking space"""
        if obj.parking_space and obj.parking_space.parking_lot:
            return obj.parking_space.parking_lot.name
        return "N/A"


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
        fields = [
            'id', 'user', 'subject', 'message', 'status',
            'created_at', 'updated_at', 'assigned_to'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'assigned_to']
