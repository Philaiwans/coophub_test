# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Room, Message

User = get_user_model()


# chat/consumers.py
import json
import re
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Room, Message

User = get_user_model()

def make_display_name(user) -> str:
    # Admin
    if getattr(user, "role", "") == "admin" or getattr(user, "username", "") == "admin007":
        return "Admin"

    first = (getattr(user, "first_name", "") or "").strip()
    last = (getattr(user, "last_name", "") or "").strip()
    full = (first + " " + last).strip() or user.username

    role = getattr(user, "role", "")
    if role == "teacher":
        return f"{full} (อาจารย์)"

    if role == "student":
        sid = (getattr(user, "student_id", "") or "").strip()
        yy = sid[:2] if len(sid) >= 2 and sid[:2].isdigit() else ""
        return f"{full} ({yy})" if yy else full

    return full

def profile_url(user) -> str | None:
    try:
        if user.profile_image:
            return user.profile_image.url
    except Exception:
        pass
    return None


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_slug = self.scope["url_route"]["kwargs"]["room_slug"]
        self.room_group_name = f"chat_{self.room_slug}"
        self.user = self.scope["user"]

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        messages = await self.get_messages()
        await self.send(text_data=json.dumps({
            "type": "chat_history",
            "messages": messages
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        # payload ที่เราจะส่งจากหน้า room.html:
        # { message_type: "text|image|file|link", content: "...", attachment_url: "...", attachment_name: "..." }
        message_type = data.get("message_type", "text")
        content = (data.get("content") or "").strip()
        attachment_url = data.get("attachment_url")
        attachment_name = data.get("attachment_name")

        # fallback: ถ้าส่ง message เดิมมา
        if not content and data.get("message"):
            content = (data.get("message") or "").strip()

        # auto-detect link (ถ้าคนพิมพ์ URL มาเฉย ๆ)
        if message_type == "text" and content:
            if re.search(r"(https?://\S+)", content):
                # ให้ยังเป็น text ก็ได้ แต่ถ้าอยากเป็น link:
                # message_type = "link"
                pass

        if not self.user.is_authenticated:
            return

        saved = await self.save_message(
            user_id=self.user.id,
            message_type=message_type,
            content=content,
            attachment_url=attachment_url,
            attachment_name=attachment_name,
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "display_name": saved["display_name"],
                "profile_image": saved["profile_image"],
                "message_type": saved["message_type"],
                "content": saved["content"],
                "attachment_url": saved["attachment_url"],
                "attachment_name": saved["attachment_name"],
                "timestamp": saved["timestamp"],
                "is_me_id": saved["user_id"],  # ไว้เทียบฝั่ง js
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "display_name": event["display_name"],
            "profile_image": event["profile_image"],
            "message_type": event["message_type"],
            "content": event["content"],
            "attachment_url": event["attachment_url"],
            "attachment_name": event["attachment_name"],
            "timestamp": event["timestamp"],
            "is_me_id": event["is_me_id"],
        }))

    @database_sync_to_async
    def save_message(self, user_id, message_type, content, attachment_url, attachment_name):
        user = User.objects.get(id=user_id)
        room = Room.objects.get(slug=self.room_slug)

        msg = Message.objects.create(
            room=room,
            user=user,
            message_type=message_type,
            content=content or "",
            attachment_url=attachment_url,
            attachment_name=attachment_name,
        )

        return {
            "user_id": user.id,
            "display_name": make_display_name(user),
            "profile_image": profile_url(user),
            "message_type": msg.message_type,
            "content": msg.content,
            "attachment_url": msg.attachment_url,
            "attachment_name": msg.attachment_name,
            "timestamp": msg.timestamp.isoformat(),
        }

    @database_sync_to_async
    def get_messages(self):
        room = Room.objects.get(slug=self.room_slug)
        qs = Message.objects.filter(room=room).select_related("user").order_by("-timestamp")[:50]
        messages = []
        for m in reversed(list(qs)):
            messages.append({
                "user_id": m.user.id,
                "display_name": make_display_name(m.user),
                "profile_image": profile_url(m.user),
                "message_type": m.message_type,
                "content": m.content,
                "attachment_url": m.attachment_url,
                "attachment_name": m.attachment_name,
                "timestamp": m.timestamp.isoformat(),
            })
        return messages


class ChatbotConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_slug = self.scope["url_route"]["kwargs"]["slug"]
        self.group_name = f"chatbot_{self.room_slug}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.send(text_data=json.dumps({
            "sender": "bot",
            "message": "สวัสดีครับ 👋 ผมคือ CoopHub Bot พิมพ์คำถามมาได้เลย"
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        user_message = (data.get("message") or "").strip()
        if not user_message:
            return

        reply = self.bot_logic(user_message)

        await self.send(text_data=json.dumps({
            "sender": "bot",
            "message": reply
        }))

    def bot_logic(self, msg: str) -> str:
        m = msg.lower()

        # ตัวอย่าง FAQ ที่คุณอยากได้
        if "สวัสดี" in m or "hello" in m or "hi" in m:
            return "สวัสดีครับ 😊 มีอะไรให้ช่วยไหม"

        if "เกรด" in m and ("ขั้นต่ำ" in m or "ขั้นต่ำเท่าไหร่" in m):
            return "เกรดขั้นต่ำโดยทั่วไปแนะนำ 2.00 ขึ้นไป (ถ้าแต่ละสาขากำหนดต่างกัน ให้รอแอดมินยืนยันนะครับ)"

        if "สมัคร" in m or "register" in m:
            return "การสมัครสมาชิก: ไปที่หน้า Register แล้วกรอกข้อมูลให้ครบ จากนั้นยืนยันอีเมลครับ"

        if "โพสต์" in m or "ประกาศ" in m:
            return "การสร้างโพสต์ฝึกงาน: กดเมนู 'สร้างโพสต์' แล้วกรอกข้อมูลให้ครบครับ"

        # ไม่รู้ → ให้รอแอดมิน
        return "คำถามนี้ผมยังตอบไม่ได้ครับ 🙏 ขอให้รอแอดมินมาตอบในห้อง Community/หรือแจ้งแอดมินได้เลยครับ"
