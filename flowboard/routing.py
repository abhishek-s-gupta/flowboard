from django.urls import re_path
from projects import consumers as project_consumers
from notifications import consumers as notification_consumers

websocket_urlpatterns = [
    re_path(r'^ws/board/(?P<project_id>\d+)/$', project_consumers.BoardConsumer.as_asgi()),
    re_path(r'^ws/notifications/$', notification_consumers.NotificationConsumer.as_asgi()),
]
