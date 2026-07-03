from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('pledge-ticket/<int:loan_id>/', views.pledge_ticket_pdf, name='pledge_ticket'),
    path('receipt/<int:repayment_id>/', views.repayment_receipt_pdf, name='repayment_receipt'),
]
