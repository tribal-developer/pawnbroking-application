from django.urls import path
from . import views

app_name = 'loans'

urlpatterns = [
    path('', views.loan_list, name='list'),
    path('new/<int:customer_id>/', views.loan_create, name='create'),
    path('<int:pk>/', views.loan_detail, name='detail'),
    path('<int:pk>/repay/', views.record_repayment, name='repay'),
    path('<int:pk>/renew/', views.renew_loan, name='renew'),
]
