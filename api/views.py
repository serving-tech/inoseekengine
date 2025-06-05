from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from users.models import User
from cars.models import Car
from parking_lots.models import ParkingSpace
from parking_transactions.models import ParkingTransaction
from alerts.models import Alert
from payments.models import PaymentTransaction, CentralTill, ClientTill
from .serializers import UserSerializer, CarSerializer, ParkingTransactionSerializer, AlertSerializer, PaymentTransactionSerializer
import random
import string
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings

# Initialize Brevo API client
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = settings.BREVO_API_KEY
brevo_api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        name = request.data.get('name')
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')

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

        try:
            user = User(
                email=email,
                name=name,
                phone_number=phone_number,
                password_hash=make_password(password),
                balance=0.0,
                is_email_verified=False,
                otp=''.join(random.choices(string.digits, k=6)),
                otp_created_at=timezone.now()
            )
            user.save()

            print(f"Generated OTP for {email}: {user.otp}")  # Debug log

            # Send OTP email via Brevo
            try:
                send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                    to=[{"email": email, "name": name}],
                    sender={"email": settings.BREVO_SENDER_EMAIL, "name": "Your Website Team"},
                    template_id=settings.BREVO_OTP_TEMPLATE_ID,
                    params={"FIRSTNAME": name, "OTP_CODE": user.otp}
                )
                brevo_api_instance.send_transac_email(send_smtp_email)
                print(f"OTP email sent to {email}")  # Debug log
            except ApiException as e:
                print(f"Error sending OTP email: {str(e)}")  # Log error but don’t block registration
                return Response(
                    {'status': 'success', 'message': 'Registration successful, OTP email failed to send. Please resend OTP.', 'user_id': user.id},
                    status=status.HTTP_201_CREATED
                )

            return Response({
                'status': 'success',
                'message': 'Registration successful, please verify OTP',
                'user_id': user.id,
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"Error registering user: {str(e)}")  # Debug log
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get('user_id')
        otp = request.data.get('otp')

        print(f"Verifying OTP - user_id: {user_id}, otp: {otp}")  # Debug log

        if not all([user_id, otp]):
            return Response(
                {'status': 'error', 'message': 'User ID and OTP are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)

            if not user.otp:
                return Response(
                    {'status': 'error', 'message': 'No OTP found for this user'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if user.otp != str(otp):
                return Response(
                    {'status': 'error', 'message': 'Invalid OTP'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if user.otp_created_at and user.otp_created_at < (timezone.now() - timezone.timedelta(minutes=5)):
                return Response(
                    {'status': 'error', 'message': 'OTP expired'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Activate user and verify email
            user.is_active = True
            user.is_email_verified = True
            user.otp = None  # Clear OTP
            user.otp_created_at = None  # Clear timestamp
            user.save()

            # Send welcome email via Brevo
            try:
                send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                    to=[{"email": user.email, "name": user.name}],
                    sender={"email": settings.BREVO_SENDER_EMAIL, "name": "Your Website Team"},
                    template_id=settings.BREVO_WELCOME_TEMPLATE_ID,
                    params={"FIRSTNAME": user.name}
                )
                brevo_api_instance.send_transac_email(send_smtp_email)
                print(f"Welcome email sent to {user.email}")  # Debug log
            except ApiException as e:
                print(f"Error sending welcome email: {str(e)}")  # Log error but don’t block verification

            # Return full user data
            return Response({
                'status': 'success',
                'message': 'OTP verified',
                'user_id': user.id,
                'name': user.name,
                'email': user.email,
                'phone_number': user.phone_number,
                'balance': user.balance,
                'is_email_verified': user.is_email_verified,
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {'status': 'error', 'message': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"Error verifying OTP: {str(e)}")  # Debug log
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
                return Response(
                    {'status': 'error', 'message': 'User already verified'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate new OTP
            otp = ''.join(random.choices(string.digits, k=6))
            user.otp = otp
            user.otp_created_at = timezone.now()
            user.save()

            print(f"Resent OTP for {email}: {otp}")  # Debug log

            # Send OTP resend email via Brevo
            try:
                send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                    to=[{"email": email, "name": user.name}],
                    sender={"email": settings.BREVO_SENDER_EMAIL, "name": "Your Website Team"},
                    template_id=settings.BREVO_OTP_RESEND_TEMPLATE_ID,
                    params={"FIRSTNAME": user.name, "OTP_CODE": otp}
                )
                brevo_api_instance.send_transac_email(send_smtp_email)
                print(f"OTP resend email sent to {email}")  # Debug log
            except ApiException as e:
                print(f"Error sending OTP resend email: {str(e)}")  # Log error but don’t block resend
                return Response(
                    {'status': 'success', 'message': 'OTP resent successfully, but email failed to send'},
                    status=status.HTTP_200_OK
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
            print(f"Error resending OTP: {str(e)}")  # Debug log
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class SetPasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        password = request.data.get('password')
        try:
            user = request.user
            user.password_hash = make_password(password)
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
            if check_password(password, user.password_hash):
                if user.is_email_verified:
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'status': 'success',
                        'message': 'Login successful',
                        'access_token': str(refresh.access_token),
                        'refresh_token': str(refresh),
                        'user': UserSerializer(user).data
                    })
                return Response({'status': 'error', 'message': 'Email not verified'})
            return Response({'status': 'error', 'message': 'Invalid password'})
        except User.DoesNotExist:
            return Response({'status': 'error', 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

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
        transactions = ParkingTransaction.objects.filter(car__user=request.user)
        return Response(ParkingTransactionSerializer(transactions, many=True).data)

class PaymentTransactionListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        payments = PaymentTransaction.objects.filter(user=request.user)
        return Response(PaymentTransactionSerializer(payments, many=True).data)

class TopUpAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        amount = request.data.get('amount')
        try:
            payment = PaymentTransaction.objects.create(
                user=request.user,
                transaction_type='top-up',
                amount=amount,
                mpesa_transaction_id=f"MPESA_{random.randint(100000, 999999)}",
                status='pending'
            )
            return Response({
                'status': 'success',
                'message': 'Top-up initiated',
                'payment': PaymentTransactionSerializer(payment).data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

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

class ExitVehicle(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        transaction_id = request.data.get('transaction_id')
        try:
            transaction = ParkingTransaction.objects.get(transaction_id=transaction_id, status='ongoing')
            transaction.exit_time = timezone.now()
            transaction.duration = transaction.exit_time - transaction.entry_time
            hours = transaction.duration.total_seconds() / 3600
            transaction.fee = (hours / 24) * 300
            transaction.cyyks_share = transaction.fee * 0.15
            transaction.client_share = transaction.fee * 0.85
            transaction.status = 'completed'
            transaction.save()
            transaction.car.user.balance -= transaction.fee
            transaction.car.user.save()
            central_till = CentralTill.objects.first() or CentralTill.objects.create()
            central_till.balance += transaction.cyyks_share
            central_till.save()
            client_till = ClientTill.objects.get(parking_lot=transaction.parking_space.parking_lot)
            client_till.balance += transaction.client_share
            client_till.save()
            payment = PaymentTransaction.objects.create(
                user=transaction.car.user,
                parking_transaction=transaction,
                transaction_type='fee_deduction',
                amount=transaction.fee,
                status='success'
            )
            transaction.parking_space.is_occupied = False
            transaction.parking_space.save()
            return Response({
                'status': 'success',
                'message': 'Exit processed, fee deducted',
                'transaction': ParkingTransactionSerializer(transaction).data,
                'payment': PaymentTransactionSerializer(payment).data
            })
        except ParkingTransaction.DoesNotExist:
            return Response({'status': 'error', 'message': 'Transaction not found or already completed'}, status=status.HTTP_404_NOT_FOUND)