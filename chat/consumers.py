import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Room, Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_slug = self.scope['url_route']['kwargs']['room_slug']
        self.room_group_name = f'chat_{self.room_slug}'
        
        # ⭐ เก็บ user จาก session
        self.user = self.scope['user']

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        messages = await self.get_messages()
        await self.send(text_data=json.dumps({
            'type': 'chat_history',
            'messages': messages
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        
        # ⭐ ใช้ username จาก user ที่ login หรือสร้างใหม่
        if self.user.is_authenticated:
            username = self.user.username
        else:
            username = data.get('username', 'Anonymous')
            # สร้าง user ถ้ายังไม่มี
            await self.get_or_create_user(username)

        await self.save_message(username, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
                'timestamp': str(await self.get_current_time())
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def get_or_create_user(self, username):
        # ⭐ สร้าง user ถ้ายังไม่มี
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': f'{username}@example.com'}
        )
        return user

    @database_sync_to_async
    def save_message(self, username, message):
        user = User.objects.get(username=username)
        room = Room.objects.get(slug=self.room_slug)
        Message.objects.create(user=user, room=room, content=message)

    @database_sync_to_async
    def get_messages(self):
        room = Room.objects.get(slug=self.room_slug)
        messages = Message.objects.filter(room=room).order_by('-timestamp')[:50]
        return [{
            'username': msg.user.username,
            'message': msg.content,
            'timestamp': msg.timestamp.isoformat()
        } for msg in reversed(messages)]

    @database_sync_to_async
    def get_current_time(self):
        from django.utils import timezone
        return timezone.now().isoformat()