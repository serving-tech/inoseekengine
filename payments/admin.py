from django.contrib import admin

from payments.models import PaymentTransaction, CentralTill, ClientTill

#
admin.site.register(PaymentTransaction)
admin.site.register(CentralTill)
admin.site.register(ClientTill)

