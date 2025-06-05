# import cv2
# import easyocr
# import time
# from decimal import Decimal
# from datetime import timedelta
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import AllowAny
# from rest_framework import status
# from django.utils import timezone
# from alerts.models import Alert
# from parking_lots.models import ParkingSpace
# from parking_transactions.models import ParkingTransaction
# from payments.models import ClientTill, CentralTill
# from cars.models import Car
#
#
# class OCRFromIPCamera(APIView):
#     permission_classes = [AllowAny]
#
#     def get(self, request, *args, **kwargs):
#         stream_url = "http://192.168.24.199:8080/video"
#         cap = cv2.VideoCapture(stream_url)
#         if not cap.isOpened():
#             return Response({"error": "Failed to open camera stream."},
#                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#         time.sleep(2)
#         ret, frame = cap.read()
#         cap.release()
#         if not ret:
#             return Response({"error": "Failed to read frame."},
#                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         reader = easyocr.Reader(['en'])
#         results = reader.readtext(gray)
#
#         number_plate = None
#         for _, text, prob in results:
#             if prob > 0.6:
#                 plate = text.replace(" ", "").upper()
#                 if len(plate) >= 5:
#                     number_plate = plate
#                     break
#
#         if not number_plate:
#             return Response({"status": "no_plate_detected"}, status=status.HTTP_200_OK)
#
#         # Check Plate
#         try:
#             car = Car.objects.get(number_plate=number_plate)
#         except Car.DoesNotExist:
#             # Create alert
#             Alert.objects.create(
#                 parking_space=ParkingSpace.objects.first(),  # adjust assignment
#                 number_plate=number_plate,
#                 description=f"Unregistered car: {number_plate}"
#             )
#             return Response({"status": "unregistered_car", "number_plate": number_plate},
#                             status=status.HTTP_404_NOT_FOUND)
#
#         user = car.user
#         parking_fee = Decimal('300.00')
#         if user.balance < parking_fee:
#             return Response({
#                 "status": "insufficient_balance",
#                 "number_plate": number_plate,
#                 "current_balance": float(user.balance)
#             }, status=status.HTTP_402_PAYMENT_REQUIRED)
#
#         # Deduct balance
#         user.balance -= parking_fee
#         user.save()
#
#         # Create parking transaction
#         transaction = ParkingTransaction.objects.create(
#             car=car,
#             parking_space=ParkingSpace.objects.first(),  # adjust selection
#             entry_time=timezone.now(),
#             duration=timedelta(hours=1),  # placeholder duration
#             fee=parking_fee,
#             cyyks_share=parking_fee * Decimal('0.15'),
#             client_share=parking_fee * Decimal('0.85'),
#             status='completed'
#         )
#
#         # Log payment
#         transaction.paymenttransaction_set.create(
#             user=user,
#             transaction_type='fee_deduction',
#             amount=parking_fee,
#             status='success'
#         )
#
#         # Update tills
#         CentralTill.objects.update_or_create(
#             id=1, defaults={'balance': CentralTill.objects.first().balance + transaction.cyyks_share}
#         )
#         ClientTill.objects.update_or_create(
#             client=transaction.parking_space.parking_lot.client,
#             defaults={'balance': ClientTill.objects.first().balance + transaction.client_share}
#         )
#
#         return Response({
#             "status": "charged",
#             "number_plate": number_plate,
#             "amount": float(parking_fee),
#             "new_balance": float(user.balance)
#         }, status=status.HTTP_200_OK)
