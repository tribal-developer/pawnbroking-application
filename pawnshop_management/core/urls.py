from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('metal-rates/', views.metal_rate_list, name='metal_rate_list'),
    path('metal-rates/add/', views.metal_rate_create, name='metal_rate_create'),
]
