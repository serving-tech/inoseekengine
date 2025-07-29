from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.renderers import JSONRenderer
from users.models import User
from parking_lots.models import ParkingLot, ParkingSpace
from parking_transactions.models import ParkingTransaction
from api.serializers import UserSerializer, ParkingLotSerializer, ParkingTransactionSerializer
from django.db.models import Sum, Count
from rest_framework import status
from datetime import datetime, timedelta
from alerts.models import Alert
from api.serializers import AlertSerializer
from api.models import SupportTicket
from api.serializers import SupportTicketSerializer

def is_company_admin(user):
    return getattr(user, 'role', None) == 'company_admin'

class IsCompanyAdmin(BasePermission):
    def has_permission(self, request, view):
        return is_company_admin(request.user)

# 1. Dashboard (Global Overview)
class CompanyDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    renderer_classes = [JSONRenderer]
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
        response = Response({
            'kpis': kpis,
            'recent_transactions': recent_transactions,
        })
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response

# 2. Clients Management
class CompanyClientsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    renderer_classes = [JSONRenderer]
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
        response = Response(data)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response

class CompanyClientDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]
    def get(self, request, client_id):
        response = Response({"message": f"Client {client_id} details"})
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response
    def put(self, request, client_id):
        response = Response({"message": f"Client {client_id} updated"})
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response
    def delete(self, request, client_id):
        response = Response({"message": f"Client {client_id} deleted"})
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response

# 3. Locations Management
class CompanyLocationsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    renderer_classes = [JSONRenderer]
    def get(self, request):
        lots = ParkingLot.objects.all()
        response = Response(ParkingLotSerializer(lots, many=True).data)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response

class CompanyLocationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]
    def get(self, request, location_id):
        response = Response({"message": f"Location {location_id} details"})
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response
    def put(self, request, location_id):
        response = Response({"message": f"Location {location_id} updated"})
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response
    def delete(self, request, location_id):
        response = Response({"message": f"Location {location_id} deleted"})
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response

# 4. Users (Drivers)
class CompanyUsersAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    renderer_classes = [JSONRenderer]
    def get(self, request):
        users = User.objects.filter(role='driver')
        response = Response(UserSerializer(users, many=True).data)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response

class CompanyUserDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]
    def get(self, request, user_id):
        response = Response({"message": f"User {user_id} details"})
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response
    def put(self, request, user_id):
        response = Response({"message": f"User {user_id} updated"})
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response

# 5. Staff Management
class CompanyStaffAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    renderer_classes = [JSONRenderer]
    def get(self, request):
        staff = User.objects.filter(role='staff')
        response = Response(UserSerializer(staff, many=True).data)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response
    def post(self, request):
        data = request.data.copy()
        data['role'] = 'staff'
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            serializer.save(role='staff')
            response = Response(serializer.data, status=201)
        else:
            response = Response(serializer.errors, status=400)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response

class CompanyStaffDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    renderer_classes = [JSONRenderer]
    def get(self, request, staff_id):
        try:
            staff = User.objects.get(id=staff_id, role='staff')
            response = Response(UserSerializer(staff).data)
        except User.DoesNotExist:
            response = Response({'error': 'Not found'}, status=404)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response
    def put(self, request, staff_id):
        try:
            staff = User.objects.get(id=staff_id, role='staff')
            serializer = UserSerializer(staff, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                response = Response(serializer.data)
            else:
                response = Response(serializer.errors, status=400)
        except User.DoesNotExist:
            response = Response({'error': 'Not found'}, status=404)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response
    def delete(self, request, staff_id):
        try:
            staff = User.objects.get(id=staff_id, role='staff')
            staff.delete()
            response = Response(status=204)
        except User.DoesNotExist:
            response = Response({'error': 'Not found'}, status=404)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response

# 6. Parking Sessions (Live Activity)
class CompanyParkingSessionsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    renderer_classes = [JSONRenderer]
    def get(self, request):
        sessions = ParkingTransaction.objects.filter(status='ongoing')
        response = Response(ParkingTransactionSerializer(sessions, many=True).data)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response

# 7. Parking History (All Time)
class CompanyParkingHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]
    def get(self, request):
        response = Response({"message": "Parking history data (all time)"})
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response

# 8. Financial Transactions
class CompanyFinancialTransactionsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    renderer_classes = [JSONRenderer]
    def get(self, request):
        today = datetime.today().date()
        days = [today - timedelta(days=i) for i in range(30)]
        revenue_by_day = []
        for day in days:
            total = ParkingTransaction.objects.filter(
                created_at__date=day
            ).aggregate(total=Sum('fee'))['total'] or 0
            revenue_by_day.append({'date': day, 'revenue': total})
        response = Response({'revenue_by_day': revenue_by_day})
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response

# 9. Analytics & Reports
class CompanyAnalyticsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    renderer_classes = [JSONRenderer]
    def get(self, request):
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
        response = Response({'client_performance': analytics})
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response

# 10. Notifications & Alerts
class CompanyNotificationsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    renderer_classes = [JSONRenderer]
    def get(self, request):
        alerts = Alert.objects.all().order_by('-created_at')[:100]
        response = Response(AlertSerializer(alerts, many=True).data)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response

# 11. System Settings
class CompanySettingsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]
    def get(self, request):
        response = Response({"message": "System settings data"})
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response
    def put(self, request):
        response = Response({"message": "System settings updated"})
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response

# 12. Support / Helpdesk
class CompanySupportAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    renderer_classes = [JSONRenderer]
    def get(self, request):
        tickets = SupportTicket.objects.all().order_by('-created_at')[:100]
        response = Response(SupportTicketSerializer(tickets, many=True).data)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response
    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = SupportTicketSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            response = Response(serializer.data, status=201)
        else:
            response = Response(serializer.errors, status=400)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response
    def put(self, request):
        ticket_id = request.data.get('id')
        try:
            ticket = SupportTicket.objects.get(id=ticket_id)
            serializer = SupportTicketSerializer(ticket, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                response = Response(serializer.data)
            else:
                response = Response(serializer.errors, status=400)
        except SupportTicket.DoesNotExist:
            response = Response({'error': 'Not found'}, status=404)
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = 'application/json'
        response.renderer_context = {}
        return response