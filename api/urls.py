from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RegisterAPIView,
    VerifyOTPAPIView,
    ResendOTPAPIView,
    SetPasswordAPIView,
    LoginAPIView,
    UserProfileAPIView,
    UserProfileUpdateAPIView,
    CarListCreateAPIView,
    CarToggleAPIView,
    CarDeleteAPIView,
    TransactionsAPIView,
    CheckNumberPlate,
    ExitVehicle,
    InitiatePaymentAPIView,
    PaymentStatusCallbackAPIView,
    SupportTicketListCreateAPIView  # New view for SupportTicket
)

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPAPIView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPAPIView.as_view(), name='resend-otp'),
    path('set-password/', SetPasswordAPIView.as_view(), name='set-password'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('profile/', UserProfileAPIView.as_view(), name='profile'),
    path('profile/update/', UserProfileUpdateAPIView.as_view(), name='profile-update'),
    path('cars/', CarListCreateAPIView.as_view(), name='cars'),
    path('cars/<int:car_id>/toggle/', CarToggleAPIView.as_view(), name='car-toggle'),
    path('cars/<int:car_id>/delete/', CarDeleteAPIView.as_view(), name='car-delete'),
    path('transactions/', TransactionsAPIView.as_view(), name='transactions'),
    path('check-number-plate/', CheckNumberPlate.as_view(), name='check-number-plate'),
    path('exit-vehicle/', ExitVehicle.as_view(), name='exit-vehicle'),
    path('initiate-payment/', InitiatePaymentAPIView.as_view(), name='initiate-payment'),
    path('payment-status/', PaymentStatusCallbackAPIView.as_view(), name='payment-status-callback'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('support-tickets/', SupportTicketListCreateAPIView.as_view(), name='support-tickets'),

    # Mount the client API endpoints under /client/
    path('client/', include('api.client.urls')),
    # Mount the company API endpoints under /company/
    path('company/', include('api.company.urls')),
]
