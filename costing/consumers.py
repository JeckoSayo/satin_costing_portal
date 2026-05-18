import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.serializers.json import DjangoJSONEncoder

from . import services


class AuthenticatedGroupConsumer(AsyncJsonWebsocketConsumer):
    group_name = None

    @classmethod
    async def encode_json(cls, content):
        return json.dumps(content, cls=DjangoJSONEncoder)

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        initial_payload = await self.get_initial_payload()
        if initial_payload:
            await self.send_json(initial_payload)

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_json_event(self, event):
        await self.send_json(event["payload"])

    async def get_initial_payload(self):
        return None


class DashboardConsumer(AuthenticatedGroupConsumer):
    group_name = services.REALTIME_DASHBOARD_GROUP

    async def get_initial_payload(self):
        return {
            "type": "dashboard.update",
            "payload": await database_sync_to_async(services.get_dashboard_realtime_payload)(),
        }


class NotificationConsumer(AuthenticatedGroupConsumer):
    group_name = services.REALTIME_NOTIFICATION_GROUP

    async def get_initial_payload(self):
        return {
            "type": "notifications.ready",
            "payload": {"message": "Live notifications connected."},
        }


class InventoryConsumer(AuthenticatedGroupConsumer):
    group_name = services.REALTIME_INVENTORY_GROUP

    async def get_initial_payload(self):
        return {
            "type": "inventory.update",
            "payload": await database_sync_to_async(services.get_inventory_realtime_payload)(),
        }


class SalesConsumer(AuthenticatedGroupConsumer):
    group_name = services.REALTIME_SALES_GROUP

    async def get_initial_payload(self):
        return {
            "type": "sales.update",
            "payload": await database_sync_to_async(services.get_sales_realtime_payload)(),
        }
