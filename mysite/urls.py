"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from core import views

urlpatterns = [
    path('', views.display_frontpage, name='display_frontpage'),
    path('admin/', admin.site.urls),
    path('events/', views.display_events, name='display_events'),
    path('events/import/', views.import_events, name='import_events'),
    path('invoices/', views.display_invoices, name='display_invoices'),
    path('invoices/export/', views.export_invoices, name='export_invoices'),
    path('system/', views.display_system, name='display_system'),
    path('system/import/products/', views.import_and_update_products, name='import_and_update_products'),
    path('system/import/customers/', views.import_and_update_customers, name='import_and_update_customers'),
    
]
