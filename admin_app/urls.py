from django.urls import path
from . import views

app_name = 'admin_app'

urlpatterns = [
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("users/", views.admin_user_list, name="admin_user_list"),
    path("products/", views.admin_product_list, name="admin_product_list"),
    path("categories/", views.admin_category, name="admin_category"),
    path("notifications/", views.admin_notification_list,
         name="admin_notifications"),
    path("notifications/<int:log_id>/", views.admin_notification_detail,
         name="admin_notification_detail"),
    path("error_logs/", views.admin_error_logs, name="admin_error_logs"),
]
