from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RegisterAPIView, VerifyOTPAPIView, SetPasswordAPIView, LoginAPIView,
    UserProfileAPIView, UserProfileUpdateAPIView, CarListCreateAPIView,
    CarToggleAPIView, CarDeleteAPIView, ParkingTransactionListAPIView,
    PaymentTransactionListAPIView, TopUpAPIView, CheckNumberPlate, ExitVehicle
)

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPAPIView.as_view(), name='verify-otp'),
    path('set-password/', SetPasswordAPIView.as_view(), name='set-password'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('profile/', UserProfileAPIView.as_view(), name='profile'),
    path('profile/update/', UserProfileUpdateAPIView.as_view(), name='profile-update'),
    path('cars/', CarListCreateAPIView.as_view(), name='cars'),
    path('cars/<int:car_id>/toggle/', CarToggleAPIView.as_view(), name='car-toggle'),
    path('cars/<int:car_id>/delete/', CarDeleteAPIView.as_view(), name='car-delete'),
    path('transactions/', ParkingTransactionListAPIView.as_view(), name='transactions'),
    path('payments/', PaymentTransactionListAPIView.as_view(), name='payments'),
    path('topup/', TopUpAPIView.as_view(), name='topup'),
    path('check-number-plate/', CheckNumberPlate.as_view(), name='check-number-plate'),
    path('exit-vehicle/', ExitVehicle.as_view(), name='exit-vehicle'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
