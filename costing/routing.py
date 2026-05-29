from django.urls import path

from . import consumers


websocket_urlpatterns = [
    path("ws/dashboard/", consumers.DashboardConsumer.as_asgi()),
    path("ws/notifications/", consumers.NotificationConsumer.as_asgi()),
    path("ws/inventory/", consumers.InventoryConsumer.as_asgi()),
    path("ws/sales/", consumers.SalesConsumer.as_asgi()),
    path("ws/customer-queue/", consumers.CustomerQueueConsumer.as_asgi()),
    path("ws/staff-queue/", consumers.StaffQueueConsumer.as_asgi()),
]
