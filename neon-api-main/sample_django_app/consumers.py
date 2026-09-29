import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ProductUpdateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'product_updates'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Handle incoming WebSocket data
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message back to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    async def product_update(self, event):
        # Handle the product update event
        await self.send(text_data=json.dumps(event["message"]))
