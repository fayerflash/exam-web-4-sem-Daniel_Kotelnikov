from django.contrib import admin
from django.urls import path
from canteen import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('statistics/', views.admin_statistics, name='admin_statistics'),
    path('purchase-requests/', views.admin_purchase_requests, name='admin_purchase_requests'),
    path('purchase-requests/approve/<int:request_id>/', views.approve_purchase_request, name='approve_purchase_request'),
    path('purchase-requests/reject/<int:request_id>/', views.reject_purchase_request, name='reject_purchase_request'),
    path('reports/', views.admin_reports, name='admin_reports'),
    path('reports/meals/', views.report_meals, name='report_meals'),
    path('reports/costs/', views.report_costs, name='report_costs'),
    path('students/', views.admin_students, name='admin_students'),
    path('dishes/', views.admin_dishes, name='admin_dishes'),
    path('users/', views.admin_users, name='admin_users'),
]