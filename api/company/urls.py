from django.urls import path
from .views import (
    CompanyDashboardAPIView, CompanyClientsAPIView, CompanyClientDetailAPIView, CompanyLocationsAPIView, CompanyLocationDetailAPIView,
    CompanyUsersAPIView, CompanyUserDetailAPIView, CompanyStaffAPIView, CompanyStaffDetailAPIView, CompanyParkingSessionsAPIView,
    CompanyParkingHistoryAPIView, CompanyFinancialTransactionsAPIView, CompanyAnalyticsAPIView, CompanyNotificationsAPIView,
    CompanySettingsAPIView, CompanySupportAPIView
)

urlpatterns = [
    path('dashboard/', CompanyDashboardAPIView.as_view(), name='company-dashboard'),
    path('clients/', CompanyClientsAPIView.as_view(), name='company-clients'),
    path('clients/<int:client_id>/', CompanyClientDetailAPIView.as_view(), name='company-client-detail'),
    path('locations/', CompanyLocationsAPIView.as_view(), name='company-locations'),
    path('locations/<int:location_id>/', CompanyLocationDetailAPIView.as_view(), name='company-location-detail'),
    path('users/', CompanyUsersAPIView.as_view(), name='company-users'),
    path('users/<int:user_id>/', CompanyUserDetailAPIView.as_view(), name='company-user-detail'),
    path('staff/', CompanyStaffAPIView.as_view(), name='company-staff'),
    path('staff/<int:staff_id>/', CompanyStaffDetailAPIView.as_view(), name='company-staff-detail'),
    path('parking-sessions/', CompanyParkingSessionsAPIView.as_view(), name='company-parking-sessions'),
    path('parking-history/', CompanyParkingHistoryAPIView.as_view(), name='company-parking-history'),
    path('financial-transactions/', CompanyFinancialTransactionsAPIView.as_view(), name='company-financial-transactions'),
    path('analytics/', CompanyAnalyticsAPIView.as_view(), name='company-analytics'),
    path('notifications/', CompanyNotificationsAPIView.as_view(), name='company-notifications'),
    path('settings/', CompanySettingsAPIView.as_view(), name='company-settings'),
    path('support/', CompanySupportAPIView.as_view(), name='company-support'),
] 