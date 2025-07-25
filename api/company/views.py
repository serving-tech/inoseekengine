from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.models import User
from parking_lots.models import ParkingLot, ParkingSpace
from parking_transactions.models import ParkingTransaction
from api.serializers import UserSerializer, ParkingLotSerializer, ParkingTransactionSerializer
from django.db.models import Sum, Count, Q
from rest_framework import status
from datetime import datetime, timedelta
from alerts.models import Alert
from api.serializers import AlertSerializer
from api.models import SupportTicket
from api.serializers import SupportTicketSerializer

def is_company_admin(user):
    return getattr(user, 'role', None) == 'company_admin'

class CompanyAdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not is_company_admin(request.user):
            return Response({'detail': 'Forbidden: company admin only'}, status=status.HTTP_403_FORBIDDEN)
        return super().dispatch(request, *args, **kwargs)

# 1. Dashboard (Global Overview)
class CompanyDashboardAPIView(CompanyAdminRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        total_revenue = ParkingTransaction.objects.aggregate(total=Sum('fee'))['total'] or 0
        total_users = User.objects.filter(is_email_verified=True, is_staff=False, role='driver').count()
        total_clients = User.objects.filter(role='client').count()
        total_locations = ParkingLot.objects.count()
        active_sessions = ParkingTransaction.objects.filter(status='ongoing').count()
        live_occupancy = ParkingSpace.objects.filter(is_occupied=True).count()
        recent_transactions = ParkingTransactionSerializer(ParkingTransaction.objects.order_by('-created_at')[:10], many=True).data
        kpis = {
            'total_revenue': total_revenue,
            'total_users': total_users,
            'total_clients': total_clients,
            'total_locations': total_locations,
            'active_sessions': active_sessions,
            'live_occupancy': live_occupancy,
        }
        return Response({
            'kpis': kpis,
            'recent_transactions': recent_transactions,
        })

# 2. Clients Management
class CompanyClientsAPIView(CompanyAdminRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        clients = User.objects.filter(role='client')
        data = []
        for client in clients:
            lots = ParkingLot.objects.filter(client=client)
            revenue = ParkingTransaction.objects.filter(parking_space__parking_lot__client=client).aggregate(total=Sum('fee'))['total'] or 0
            data.append({
                'client': UserSerializer(client).data,
                'total_locations': lots.count(),
                'revenue': revenue,
            })
        return Response(data)

class CompanyClientDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, client_id):
        return Response({"message": f"Client {client_id} details"})
    def put(self, request, client_id):
        return Response({"message": f"Client {client_id} updated"})
    def delete(self, request, client_id):
        return Response({"message": f"Client {client_id} deleted"})

# 3. Locations Management
class CompanyLocationsAPIView(CompanyAdminRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        lots = ParkingLot.objects.all()
        return Response(ParkingLotSerializer(lots, many=True).data)

class CompanyLocationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, location_id):
        return Response({"message": f"Location {location_id} details"})
    def put(self, request, location_id):
        return Response({"message": f"Location {location_id} updated"})
    def delete(self, request, location_id):
        return Response({"message": f"Location {location_id} deleted"})

# 4. Users (Drivers)
class CompanyUsersAPIView(CompanyAdminRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        users = User.objects.filter(role='driver')
        return Response(UserSerializer(users, many=True).data)

class CompanyUserDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, user_id):
        return Response({"message": f"User {user_id} details"})
    def put(self, request, user_id):
        return Response({"message": f"User {user_id} updated"})

# 5. Staff Management
class CompanyStaffAPIView(CompanyAdminRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        staff = User.objects.filter(role='staff')
        return Response(UserSerializer(staff, many=True).data)
    def post(self, request):
        data = request.data.copy()
        data['role'] = 'staff'
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            serializer.save(role='staff')
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class CompanyStaffDetailAPIView(CompanyAdminRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, staff_id):
        try:
            staff = User.objects.get(id=staff_id, role='staff')
        except User.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        return Response(UserSerializer(staff).data)
    def put(self, request, staff_id):
        try:
            staff = User.objects.get(id=staff_id, role='staff')
        except User.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        serializer = UserSerializer(staff, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    def delete(self, request, staff_id):
        try:
            staff = User.objects.get(id=staff_id, role='staff')
        except User.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        staff.delete()
        return Response(status=204)

# 6. Parking Sessions (Live Activity)
class CompanyParkingSessionsAPIView(CompanyAdminRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        sessions = ParkingTransaction.objects.filter(status='ongoing')
        return Response(ParkingTransactionSerializer(sessions, many=True).data)

# 7. Parking History (All Time)
class CompanyParkingHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response({"message": "Parking history data (all time)"})

# 8. Financial Transactions
class CompanyFinancialTransactionsAPIView(CompanyAdminRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        # Example: revenue by day for last 30 days
        today = datetime.today().date()
        days = [today - timedelta(days=i) for i in range(30)]
        revenue_by_day = []
        for day in days:
            total = ParkingTransaction.objects.filter(
                created_at__date=day
            ).aggregate(total=Sum('fee'))['total'] or 0
            revenue_by_day.append({'date': day, 'revenue': total})
        return Response({'revenue_by_day': revenue_by_day})

# 9. Analytics & Reports
class CompanyAnalyticsAPIView(CompanyAdminRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        # Example: client performance comparison
        clients = User.objects.filter(role='client')
        analytics = []
        for client in clients:
            revenue = ParkingTransaction.objects.filter(parking_space__parking_lot__client=client).aggregate(total=Sum('fee'))['total'] or 0
            sessions = ParkingTransaction.objects.filter(parking_space__parking_lot__client=client).count()
            analytics.append({
                'client': UserSerializer(client).data,
                'revenue': revenue,
                'sessions': sessions,
            })
        return Response({'client_performance': analytics})

# 10. Notifications & Alerts
class CompanyNotificationsAPIView(CompanyAdminRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        alerts = Alert.objects.all().order_by('-created_at')[:100]
        return Response(AlertSerializer(alerts, many=True).data)

# 11. System Settings
class CompanySettingsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response({"message": "System settings data"})
    def put(self, request):
        return Response({"message": "System settings updated"})

# 12. Support / Helpdesk
class CompanySupportAPIView(CompanyAdminRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        tickets = SupportTicket.objects.all().order_by('-created_at')[:100]
        return Response(SupportTicketSerializer(tickets, many=True).data)
    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = SupportTicketSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def put(self, request):
        ticket_id = request.data.get('id')
        try:
            ticket = SupportTicket.objects.get(id=ticket_id)
        except SupportTicket.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        serializer = SupportTicketSerializer(ticket, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400) 