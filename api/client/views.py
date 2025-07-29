from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from parking_lots.models import ParkingLot, ParkingSpace
from parking_transactions.models import ParkingTransaction
from api.serializers import ParkingLotSerializer, ParkingTransactionSerializer
from django.db.models import Sum, Count, Q
from rest_framework import status
from datetime import datetime, timedelta
from alerts.models import Alert
from api.serializers import AlertSerializer, UserSerializer
from django.contrib.auth import get_user_model
from api.models import SupportTicket
from api.serializers import SupportTicketSerializer

User = get_user_model()

class IsClientPermission(BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, 'role', None) == 'client'

# 1. Dashboard (Home Overview)
class ClientDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsClientPermission]
    def get(self, request):
        location_id = request.query_params.get('location_id')
        lots = ParkingLot.objects.filter(client=request.user)
        if location_id:
            lots = lots.filter(id=location_id)
        lot_ids = lots.values_list('id', flat=True)
        spaces = ParkingSpace.objects.filter(parking_lot__in=lot_ids)
        transactions = ParkingTransaction.objects.filter(parking_space__parking_lot__in=lot_ids)
        now_parked = spaces.filter(is_occupied=True).count()
        total_spaces = spaces.count()
        total_revenue = transactions.aggregate(total=Sum('fee'))['total'] or 0
        kpis = {
            'total_revenue': total_revenue,
            'cars_parked_now': now_parked,
            'total_spaces': total_spaces,
            'locations_active': lots.count(),
        }
        recent_transactions = ParkingTransactionSerializer(transactions.order_by('-created_at')[:10], many=True).data
        return Response({
            'kpis': kpis,
            'recent_transactions': recent_transactions,
            'locations': ParkingLotSerializer(lots, many=True).data,
        })

# 2. Locations Management
class ClientLocationsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsClientPermission]
    def get(self, request):
        lots = ParkingLot.objects.filter(client=request.user)
        return Response(ParkingLotSerializer(lots, many=True).data)
    def post(self, request):
        data = request.data.copy()
        data['client'] = request.user.id
        serializer = ParkingLotSerializer(data=data)
        if serializer.is_valid():
            serializer.save(client=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class ClientLocationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsClientPermission]
    def put(self, request, location_id):
        try:
            lot = ParkingLot.objects.get(id=location_id, client=request.user)
        except ParkingLot.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        serializer = ParkingLotSerializer(lot, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

# 3. Current Parking (Live Activity)
class ClientCurrentParkingAPIView(APIView):
    permission_classes = [IsAuthenticated, IsClientPermission]
    def get(self, request):
        location_id = request.query_params.get('location_id')
        lots = ParkingLot.objects.filter(client=request.user)
        if location_id:
            lots = lots.filter(id=location_id)
        spaces = ParkingSpace.objects.filter(parking_lot__in=lots)
        occupied = spaces.filter(is_occupied=True)
        data = [
            {
                'space_number': s.space_number,
                'location': s.parking_lot.name,
                'is_occupied': s.is_occupied,
            } for s in occupied
        ]
        return Response({
            'occupied_spaces': len(data),
            'free_spaces': spaces.count() - len(data),
            'details': data,
        })

# 4. Parking History
class ClientParkingHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated, IsClientPermission]
    def get(self, request):
        lots = ParkingLot.objects.filter(client=request.user)
        lot_ids = lots.values_list('id', flat=True)
        transactions = ParkingTransaction.objects.filter(parking_space__parking_lot__in=lot_ids)
        # Optional filters
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        plate = request.query_params.get('plate')
        if date_from:
            transactions = transactions.filter(entry_time__gte=date_from)
        if date_to:
            transactions = transactions.filter(exit_time__lte=date_to)
        if plate:
            transactions = transactions.filter(car__number_plate__icontains=plate)
        return Response(ParkingTransactionSerializer(transactions.order_by('-entry_time')[:100], many=True).data)

# 5. Financial Reports / Transactions
class ClientFinancialReportsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsClientPermission]
    def get(self, request):
        lots = ParkingLot.objects.filter(client=request.user)
        lot_ids = lots.values_list('id', flat=True)
        transactions = ParkingTransaction.objects.filter(parking_space__parking_lot__in=lot_ids)
        # Revenue by day for last 30 days
        today = datetime.today().date()
        days = [today - timedelta(days=i) for i in range(30)]
        revenue_by_day = []
        for day in days:
            total = transactions.filter(created_at__date=day).aggregate(total=Sum('fee'))['total'] or 0
            revenue_by_day.append({'date': day, 'revenue': total})
        return Response({'revenue_by_day': revenue_by_day})

# 6. Analytics & Insights
class ClientAnalyticsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsClientPermission]
    def get(self, request):
        lots = ParkingLot.objects.filter(client=request.user)
        analytics = []
        for lot in lots:
            revenue = ParkingTransaction.objects.filter(parking_space__parking_lot=lot).aggregate(total=Sum('fee'))['total'] or 0
            sessions = ParkingTransaction.objects.filter(parking_space__parking_lot=lot).count()
            analytics.append({
                'location': ParkingLotSerializer(lot).data,
                'revenue': revenue,
                'sessions': sessions,
            })
        return Response({'location_performance': analytics})

# 7. Staff Management
class ClientStaffAPIView(APIView):
    permission_classes = [IsAuthenticated, IsClientPermission]
    def get(self, request):
        staff = User.objects.filter(role='staff', parking_lots__client=request.user).distinct()
        return Response(UserSerializer(staff, many=True).data)
    def post(self, request):
        data = request.data.copy()
        data['role'] = 'staff'
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            serializer.save(role='staff')
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class ClientStaffDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsClientPermission]
    def put(self, request, staff_id):
        try:
            staff = User.objects.get(id=staff_id, role='staff', parking_lots__client=request.user)
        except User.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        serializer = UserSerializer(staff, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    def delete(self, request, staff_id):
        try:
            staff = User.objects.get(id=staff_id, role='staff', parking_lots__client=request.user)
        except User.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        staff.delete()
        return Response(status=204)

# 8. Notifications
class ClientNotificationsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsClientPermission]
    def get(self, request):
        lots = ParkingLot.objects.filter(client=request.user)
        spaces = ParkingSpace.objects.filter(parking_lot__in=lots)
        alerts = Alert.objects.filter(parking_space__in=spaces).order_by('-created_at')[:100]
        return Response(AlertSerializer(alerts, many=True).data)

# 9. Settings
class ClientSettingsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsClientPermission]
    def get(self, request):
        return Response({"message": "Client settings data"})
    def put(self, request):
        return Response({"message": "Client settings updated"})

# 10. Support / Help
class ClientSupportFAQsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsClientPermission]
    def get(self, request):
        return Response({"message": "FAQs data"})

class ClientSupportTicketsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsClientPermission]
    def get(self, request):
        tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')[:100]
        return Response(SupportTicketSerializer(tickets, many=True).data)
    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = SupportTicketSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)