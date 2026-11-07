from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list_view, name='list'),
    path('api/dropdown/', views.api_notifications_dropdown, name='api_dropdown'),
    path('api/<int:notification_id>/read/', views.api_mark_notification_read, name='api_mark_read'),
    path('api/read-all/', views.api_mark_all_read, name='api_mark_all_read'),
]
