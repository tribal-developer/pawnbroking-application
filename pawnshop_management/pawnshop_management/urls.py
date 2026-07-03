"""
Root URL configuration for the Pawnshop / Gold-Loan Management System.
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # App URLs
    path('', include('core.urls')),
    path('customers/', include('customers.urls')),
    path('loans/', include('loans.urls')),
    path('auctions/', include('auctions.urls')),
    path('documents/', include('documents.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
