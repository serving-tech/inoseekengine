from django.urls import path
from .views import (
    ClientDashboardAPIView, ClientLocationsAPIView, ClientLocationDetailAPIView, ClientCurrentParkingAPIView,
    ClientParkingHistoryAPIView, ClientFinancialReportsAPIView, ClientAnalyticsAPIView, ClientStaffAPIView,
    ClientStaffDetailAPIView, ClientNotificationsAPIView, ClientSettingsAPIView, ClientSupportFAQsAPIView,
    ClientSupportTicketsAPIView
)

urlpatterns = [
    path('dashboard/', ClientDashboardAPIView.as_view(), name='client-dashboard'),
    path('locations/', ClientLocationsAPIView.as_view(), name='client-locations'),
    path('locations/<int:location_id>/', ClientLocationDetailAPIView.as_view(), name='client-location-detail'),
    path('parking/current/', ClientCurrentParkingAPIView.as_view(), name='client-current-parking'),
    path('parking/history/', ClientParkingHistoryAPIView.as_view(), name='client-parking-history'),
    path('financial/reports/', ClientFinancialReportsAPIView.as_view(), name='client-financial-reports'),
    path('analytics/', ClientAnalyticsAPIView.as_view(), name='client-analytics'),
    path('staff/', ClientStaffAPIView.as_view(), name='client-staff'),
    path('staff/<int:staff_id>/', ClientStaffDetailAPIView.as_view(), name='client-staff-detail'),
    path('notifications/', ClientNotificationsAPIView.as_view(), name='client-notifications'),
    path('settings/', ClientSettingsAPIView.as_view(), name='client-settings'),
    path('support/faqs/', ClientSupportFAQsAPIView.as_view(), name='client-support-faqs'),
    path('support/tickets/', ClientSupportTicketsAPIView.as_view(), name='client-support-tickets'),
] 