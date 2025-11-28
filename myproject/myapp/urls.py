from . import views
from django.urls import path

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('admin_login/', views.admin_login, name='admin_login'),
    path('index/', views.index, name='index'),
    path('normalRequest/', views.normalRequest, name='normalRequest'),
    path('adminDashboard/', views.adminDashboard, name='adminDashboard'),
    path('addEmployees/', views.addEmployees, name='addEmployees'),
    path('removeEmployee/<int:emp_id>/', views.removeEmployee, name='removeEmployee'),
    path('request/', views.request, name='request'),
    path('employeeDashboard/', views.employeeDashboard, name='employeeDashboard'),

    path('requestApproval/', views.requestApproval, name='requestApproval'),
    path('approve-requisition/<int:requisition_id>/', views.approve_requisition, name='approve_requisition'),
    path('deny-requisition/<int:requisition_id>/', views.deny_requisition, name='deny_requisition'),
    path('forward-requisition/<int:requisition_id>/', views.forward_requisition, name='forward_requisition'),


    path('inventory-dashboard/', views.inventory_dashboard, name='inventory_dashboard'),
    path('inventory-dashboard/stock-in/', views.stock_in_view, name='stock_in'),
    path('inventory-dashboard/stock-out/', views.stock_out_view, name='stock_out'),
    path('inventory-dashboard/add-product/', views.add_product, name='add_product'),
    path('inventory-dashboard/balance/', views.balance, name='balance'),
]