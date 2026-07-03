from django.urls import path
from . import views

app_name = 'auctions'

urlpatterns = [
    path('', views.auction_list, name='list'),
    path('eligible/', views.auction_eligible_list, name='eligible_list'),
    path('new/<int:loan_id>/', views.auction_create, name='create'),
]
