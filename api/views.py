from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from users.models import User
from cars.models import Car
from parking_lots.models import ParkingSpace
from parking_transactions.models import ParkingTransaction
from alerts.models import Alert
from .serializers import UserSerializer, CarSerializer, ParkingTransactionSerializer, AlertSerializer
import random
import string
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings
import logging
import requests
from parking_transactions.models import ParkingTransaction
from parking_lots.models import ParkingLot, ParkingSpace

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize Brevo API client (moved outside class)
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = settings.BREVO_API_KEY
brevo_api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

User = get_user_model()

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        name = request.data.get('name')
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')

        logger.info(f"Registering user - email: {email}, phone: {phone_number}")

        if not all([name, email, phone_number, password]):
            return Response(
                {'status': 'error', 'message': 'All fields are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {'status': 'error', 'message': 'Email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(phone_number=phone_number).exists():
            return Response(
                {'status': 'error', 'message': 'Phone number already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.create_user(
                email=email,
                name=name,
                phone_number=phone_number,
                password=password,
            )
            otp = ''.join(random.choices(string.digits, k=6))
            user.set_otp(otp)  # Use set_otp to hash and set OTP
            user.save()

            logger.info(f"Generated OTP for {email}: {otp}")

            try:
                send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                    to=[{"email": email, "name": name}],
                    sender={"email": settings.BREVO_SENDER_EMAIL, "name": "inoseek Team"},
                    template_id=settings.BREVO_OTP_TEMPLATE_ID,
                    params={"FIRSTNAME": name, "OTP_CODE": otp}
                )
                brevo_api_instance.send_transac_email(send_smtp_email)
                logger.info(f"OTP email sent to {email}")
            except ApiException as e:
                logger.error(f"Error sending OTP email: {str(e)}, Status: {e.status}, Body: {e.body}")
                user.delete()
                return Response(
                    {'status': 'error', 'message': 'Failed to send OTP email'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response({
                'status': 'success',
                'message': 'User registered successfully. Check your email for OTP.',
                'user_id': str(user.id),
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get('user_id')
        otp = request.data.get('otp')

        logger.info(f"Verifying OTP - user_id: {user_id}, otp: {otp}, current_time: {timezone.now()}")

        if not all([user_id, otp]):
            return Response(
                {'status': 'error', 'message': 'User ID and OTP are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)
            logger.info(f"User found: {user.email}, otp: {user.otp}, created_at: {user.otp_created_at}, is_active: {user.is_active}")

            if not user.otp:
                return Response(
                    {'status': 'error', 'message': 'No OTP found for this user'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ✅ Corrected password check
            if not check_password(str(otp), user.otp):
                logger.warning(f"Invalid OTP attempt for user {user.email}, provided: {otp}, stored: {user.otp}, created_at: {user.otp_created_at}")
                return Response(
                    {'status': 'error', 'message': 'Invalid OTP'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ✅ Check if OTP expired
            if user.otp_created_at and user.otp_created_at < (timezone.now() - timezone.timedelta(minutes=5)):
                logger.warning(f"OTP expired for user {user.email}, created_at: {user.otp_created_at}, now: {timezone.now()}")
                return Response(
                    {'status': 'error', 'message': 'OTP expired'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ✅ Mark user as verified
            user.is_active = True
            user.is_email_verified = True
            user.otp = None
            user.otp_created_at = None
            user.save()
            logger.info(f"User {user.email} verified successfully")

            # ✅ Optional: Send Welcome Email
            try:
                send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                    to=[{"email": user.email, "name": user.name}],
                    sender={"email": settings.BREVO_SENDER_EMAIL, "name": "inoseek Team"},
                    template_id=settings.BREVO_WELCOME_TEMPLATE_ID,
                    params={"FIRSTNAME": user.name}
                )
                brevo_api_instance.send_transac_email(send_smtp_email)
                logger.info(f"Welcome email sent to {user.email}")
            except ApiException as e:
                logger.error(f"Error sending welcome email: {str(e)}, Status: {e.status}, Body: {e.body}")

            return Response({
                'status': 'success',
                'message': 'OTP verified',
                'user_id': str(user.id),
                'name': user.name,
                'email': user.email,
                'phone_number': user.phone_number,
                'balance': str(user.balance),
                'is_email_verified': user.is_email_verified,
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            logger.error(f"User not found for user_id: {user_id}")
            return Response(
                {'status': 'error', 'message': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error verifying OTP: {str(e)}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class ResendOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response(
                {'status': 'error', 'message': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
            if user.is_active:
                logger.info(f"Resend OTP attempt for already verified user: {email}")
                return Response(
                    {'status': 'error', 'message': 'User already verified. Please log in.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if user.otp_created_at and (timezone.now() - user.otp_created_at).total_seconds() < 30:
                return Response(
                    {'status': 'error', 'message': 'Please wait 30 seconds before requesting a new OTP'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            otp = ''.join(random.choices(string.digits, k=6))
            user.set_otp(otp)  # Use set_otp to hash and set OTP
            user.save()
            logger.info(f"Resent OTP for {email}: [REDACTED], created_at: {user.otp_created_at}")

            try:
                send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                    to=[{"email": email, "name": user.name}],
                    sender={"email": settings.BREVO_SENDER_EMAIL, "name": "inoseek Team"},
                    template_id=settings.BREVO_OTP_RESEND_TEMPLATE_ID,
                    params={"FIRSTNAME": user.name, "OTP_CODE": otp}
                )
                brevo_api_instance.send_transac_email(send_smtp_email)
                logger.info(f"OTP resend email sent to {email} with OTP: {otp}")
            except ApiException as e:
                logger.error(f"Error sending OTP resend email: {str(e)}, Status: {e.status}, Body: {e.body}")
                return Response(
                    {'status': 'error', 'message': 'Failed to resend OTP email. Please try again later.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            return Response(
                {'status': 'success', 'message': 'OTP resent successfully'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error resending OTP: {str(e)}")
            return Response(
                {'status': 'error', 'message': 'An unexpected error occurred. Please try again.'},
                status=status.HTTP_400_BAD_REQUEST
            )

class SetPasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        password = request.data.get('password')
        try:
            user = request.user
            user.password = make_password(password)  # Correctly update password
            user.save()
            return Response({'status': 'success', 'message': 'Password set successfully'})
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)})

class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'status': 'error', 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if not user.check_password(password):
            return Response({'status': 'error', 'message': 'Invalid password'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_email_verified:
            return Response({'status': 'error', 'message': 'Email not verified'}, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        return Response({
            'status': 'success',
            'message': 'Login successful',
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

class UserProfileUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        data = request.data
        serializer = UserSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Profile updated successfully',
                'user_id': user.id,
                'name': user.name,
                'email': user.email,
                'phone_number': user.phone_number,
                'balance': user.balance,
                'is_email_verified': user.is_email_verified
            }, status=status.HTTP_200_OK)
        return Response({
            'status': 'error',
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class CarListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cars = Car.objects.filter(user=request.user)
        return Response(CarSerializer(cars, many=True).data)

    def post(self, request):
        data = request.data
        data['user'] = request.user.id
        serializer = CarSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CarToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, car_id):
        try:
            car = Car.objects.get(car_id=car_id, user=request.user)
            car.is_active = not car.is_active
            car.save()
            return Response(CarSerializer(car).data, status=status.HTTP_200_OK)
        except Car.DoesNotExist:
            return Response({'status': 'error', 'message': 'Car not found'}, status=status.HTTP_404_NOT_FOUND)

class CarDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, car_id):
        try:
            car = Car.objects.get(car_id=car_id, user=request.user)
            car.delete()
            return Response({'status': 'success', 'message': 'Car deleted'}, status=status.HTTP_204_NO_CONTENT)
        except Car.DoesNotExist:
            return Response({'status': 'error', 'message': 'Car not found'}, status=status.HTTP_404_NOT_FOUND)

class ParkingTransactionListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = ParkingTransaction.objects.filter(user=request.user)
        serializer = ParkingTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import requests
import logging
import uuid

logger = logging.getLogger(__name__)

class InitiatePaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        amount = request.data.get("amount")
        phone = request.data.get("phone")
        parking_transaction_id = request.data.get("parking_transaction_id")

        # Validate input
        if not amount or not phone:
            return Response({
                "status": "error",
                "message": "Amount and phone number are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than zero")
        except (ValueError, TypeError):
            return Response({
                "status": "error",
                "message": "Invalid amount format"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Generate order ID and transaction ID
        order_id = (
            f"topup-{user.id}-{int(timezone.now().timestamp())}"
            if not parking_transaction_id
            else f"park-{parking_transaction_id}"
        )
        transaction_id = str(uuid.uuid4())

        # For top-ups, use a default ParkingSpace and nullable Car
        if not parking_transaction_id:
            default_lot, _ = ParkingLot.objects.get_or_create(
                name="Top-up Lot",
                defaults={"location": "N/A", "total_spaces": 0}
            )
            default_space, _ = ParkingSpace.objects.get_or_create(
                parking_lot=default_lot,
                space_number="TOPUP",
                defaults={"is_occupied": False}
            )
            car = Car.objects.filter(user=user, is_active=True).first()
        else:
            try:
                transaction = ParkingTransaction.objects.get(
                    id=parking_transaction_id, car__user=user, status='ongoing'
                )
                default_space = transaction.parking_space
                car = transaction.car
            except ParkingTransaction.DoesNotExist:
                return Response({
                    "status": "error",
                    "message": "Invalid or unauthorized parking transaction"
                }, status=status.HTTP_400_BAD_REQUEST)

        # Prepare payment payload
        payload = {
            "transaction_id": transaction_id,
            "order_id": order_id,
            "user_id": str(user.id),
            "amount": f"{amount:.2f}",  # Decimal string, e.g., "100.00"
            "commission": "0.00",  # Required, adjust per business logic
            "disbursement_amount": f"{amount:.2f}",  # Required, match amount
            "client_till_number": settings.CLIENT_TILL_NUMBER or "174379",
            "status": "PENDING"  # Required
        }

        try:
            payment_api_url = f"{settings.PAYMENTS_API_URL}/api/v1/payments/process/"
            headers = {"Content-Type": "application/json"}  # No auth, as endpoint is open

            logger.info(f"Sending payment request to {payment_api_url} with payload: {payload}, headers: {headers}")
            response = requests.post(payment_api_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            payment_data = response.json()
            logger.info(f"Payment response: {response.status_code}, Body: {payment_data}")

            if response.status_code in (200, 201):
                if not parking_transaction_id:
                    ParkingTransaction.objects.create(
                        car=car,
                        parking_space=default_space,
                        entry_time=timezone.now(),
                        fee=amount,
                        status='topup',
                        created_at=timezone.now(),
                    )
                    user.balance = (user.balance or Decimal('0')) + amount
                    user.save()
                else:
                    transaction.fee = amount
                    transaction.status = 'completed'
                    transaction.exit_time = timezone.now()
                    transaction.duration = transaction.exit_time - transaction.entry_time
                    transaction.save()

                return Response({
                    "status": "success",
                    "message": "Payment initiated successfully",
                    "data": payment_data
                }, status=status.HTTP_201_CREATED)

            else:
                logger.error(f"Payment engine error: Status {response.status_code}, Body: {response.text}, Headers: {response.headers}")
                return Response({
                    "status": "error",
                    "message": "Payment engine returned an error",
                    "details": payment_data.get('message', response.text)
                }, status=response.status_code)

        except requests.exceptions.HTTPError as e:
            logger.error(f"Payment HTTP error: {str(e)}, Response: {e.response.text if e.response else 'No response'}, Headers: {e.response.headers if e.response else 'No headers'}")
            return Response({
                "status": "error",
                "message": "Failed to connect to payment service",
                "details": f"{str(e)}: {e.response.text if e.response else 'No response'}"
            }, status=status.HTTP_502_BAD_GATEWAY)
        except requests.exceptions.RequestException as e:
            logger.error(f"Payment request failed: {str(e)}")
            return Response({
                "status": "error",
                "message": "Failed to connect to payment service",
                "details": str(e)
            }, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response({
                "status": "error",
                "message": "An unexpected error occurred",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentStatusCallbackAPIView(APIView):
    def post(self, request):
        data = request.data
        try:
            parking_transaction = ParkingTransaction.objects.get(id=data["parking_transaction_id"])
            parking_transaction.payment_status = data["status"]
            parking_transaction.mpesa_transaction_id = data.get("mpesa_transaction_id")
            parking_transaction.save()
            return Response({"message": "Status updated"}, status=status.HTTP_200_OK)
        except ParkingTransaction.DoesNotExist:
            return Response({"error": "Parking transaction not found"}, status=status.HTTP_404_NOT_FOUND)


class CheckNumberPlate(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        number_plate = request.data.get('number_plate')
        parking_space_id = request.data.get('parking_space_id')

        if not number_plate or not parking_space_id:
            return Response({
                'status': 'error',
                'message': 'Number plate and parking space ID are required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            parking_space = ParkingSpace.objects.get(id=parking_space_id)
            car = Car.objects.get(number_plate__iexact=number_plate)

            if parking_space.is_occupied:
                return Response({
                    'status': 'error',
                    'message': 'Parking space already occupied'
                }, status=status.HTTP_400_BAD_REQUEST)

            if car.user.balance < 300:
                return Response({
                    'status': 'error',
                    'message': 'Insufficient balance'
                }, status=status.HTTP_400_BAD_REQUEST)

            parking_space.is_occupied = True
            parking_space.save()

            transaction = ParkingTransaction.objects.create(
                car=car,
                parking_space=parking_space,
                entry_time=timezone.now(),
                status='ongoing'
            )

            return Response({
                'status': 'success',
                'message': 'Vehicle registered, entry logged',
                'transaction': ParkingTransactionSerializer(transaction).data
            }, status=status.HTTP_200_OK)

        except Car.DoesNotExist:
            try:
                parking_space = ParkingSpace.objects.get(id=parking_space_id)
            except ParkingSpace.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Invalid parking space'
                }, status=status.HTTP_400_BAD_REQUEST)

            alert = Alert.objects.create(
                parking_space=parking_space,
                number_plate=number_plate,
                description=f"Unregistered car with number plate {number_plate}",
                status='unresolved'
            )

            return Response({
                'status': 'alert',
                'message': 'Unregistered vehicle, alert logged',
                'alert': AlertSerializer(alert).data
            }, status=status.HTTP_404_NOT_FOUND)

        except ParkingSpace.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Parking space not found'
            }, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils import timezone
from .serializers import ParkingTransactionSerializer
import requests
from decimal import Decimal

class ExitVehicle(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        transaction_id = request.data.get('transaction_id')

        try:
            transaction = ParkingTransaction.objects.get(transaction_id=transaction_id, payment_status='PENDING')

            # Calculate fee
            transaction.exit_time = timezone.now()
            transaction.duration = transaction.exit_time - transaction.check_in_time
            hours = transaction.duration.total_seconds() / 3600
            daily_rate = Decimal(300)
            fee = (Decimal(hours) / Decimal(24)) * daily_rate
            fee = round(fee, 2)

            transaction.total_amount = fee
            transaction.save()

            # Send payment initiation request to Payments Backend
            payment_payload = {
                "order_id": transaction.id,  # used as parking_transaction_id in payments
                "user_id": transaction.user.id,
                "amount": str(fee),
                "client_till_number": "174379",  # Replace if dynamic
                "phone_number": transaction.user.phone  # Assumes user model has a `phone` field
            }

            response = requests.post(
                url="https://inoseekpay.vercel.app/v1/api/payments/process/",
                json=payment_payload,
                timeout=10
            )

            if response.status_code != 201:
                return Response({
                    "status": "error",
                    "message": "Failed to initiate payment",
                    "details": response.json()
                }, status=response.status_code)

            return Response({
                "status": "success",
                "message": "Exit processed. Payment initiation sent.",
                "transaction": ParkingTransactionSerializer(transaction).data
            }, status=status.HTTP_200_OK)

        except ParkingTransaction.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Transaction not found or already completed'
            }, status=status.HTTP_404_NOT_FOUND)


class TransactionsAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ParkingTransactionSerializer

    def get_queryset(self):
        return ParkingTransaction.objects.filter(car__user=self.request.user).order_by('-created_at')