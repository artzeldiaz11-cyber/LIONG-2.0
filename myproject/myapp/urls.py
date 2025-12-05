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

    # ADMIN DASHBOARD URLs
    path('requestApproval/', views.requestApproval, name='requestApproval'),
    path('approve-requisition/<int:requisition_id>/', views.approve_requisition, name='approve_requisition'),
    path('deny-requisition/<int:requisition_id>/', views.deny_requisition, name='deny_requisition'),
    path('admin-requisition/view/<int:req_id>/', views.admin_requisition_view, name="admin_requisition_view"),
    path('admin-dashboard/requestApproval/', views.requestApproval, name='requestApproval'),

    # INVENTORY DASHBOARD URLs
    path('inventory-dashboard/', views.inventory_dashboard, name='inventory_dashboard'),
    path('inventory-dashboard/stock-in/', views.stock_in_view, name='stock_in'),
    path('inventory-dashboard/stock-out/', views.stock_out_view, name='stock_out'),
    path('inventory-dashboard/add-product/', views.add_product, name='add_product'),
    path('inventory-dashboard/balance/', views.balance, name='balance'),
    path('inventory-dashboard/approved_requisitions/', views.inventory_approved_requisitions, name='inventory_approved_requisitions'),
    path('inventory-partial-approve/<int:requisition_id>/', views.inventory_partial_approve, name='inventory_partial_approve'),
    path('inventory-fulfill-stock/<int:requisition_id>/', views.inventory_fulfill_from_stock, name='inventory_fulfill_stock'),
    path('inventory-requisition/view/<int:req_id>/', views.inventory_requisition_view, name="inventory_requisition_view"),

    # Employee Panel URLs
    path('employeeDashboard/', views.employeeDashboard, name='employeeDashboard'),
    path('request/', views.request, name='request'),
    path('requestHistory/', views.requestHistory, name='requestHistory'),
    path('notifications/', views.notifications, name='notifications'),
    path('settings/', views.settings, name='settings'),
]
