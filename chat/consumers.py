        # =========================
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
        m = msg.lower().strip()

        # =========================
        # ทักทาย
        # =========================
        if (
            "สวัสดี" in m
            or "หวัดดี" in m
            or "hello" in m
            or "hi" in m
        ):
            return (
                "สวัสดีครับ 😊 ผมคือ CoopHub Bot\n"
                "สามารถสอบถามข้อมูลเกี่ยวกับสหกิจศึกษาได้ เช่น\n"
                "• คุณสมบัตินักศึกษาสหกิจศึกษา\n"
                "• เกรดขั้นต่ำ\n"
                "• การสมัครสหกิจศึกษา\n"
                "• การเตรียมความพร้อม\n"
                "• ระยะเวลาปฏิบัติงาน\n"
                "• การนิเทศงาน\n"
                "• รายงานสหกิจศึกษา\n"
                "• ค่าตอบแทนและสวัสดิการ"
            )

        # =========================
        # สหกิจศึกษาคืออะไร
        # =========================
        if (
            "สหกิจศึกษาคืออะไร" in m
            or "สหกิจคืออะไร" in m
            or "สหกิจคือ" in m
            or "ความหมายสหกิจ" in m
            or "cooperative education" in m
        ):
            return (
                "สหกิจศึกษา (Cooperative Education) เป็นระบบการศึกษาที่ "
                "ผสมผสานการเรียนกับการปฏิบัติงาน (Work Integrated Learning) "
                "เพื่อให้นักศึกษาได้รับประสบการณ์จริงจากสถานประกอบการ "
                "และเตรียมความพร้อมก่อนเข้าสู่การทำงานครับ"
            )

        # =========================
        # คุณสมบัตินักศึกษาสหกิจ
        # =========================
        if (
            "คุณสมบัติสหกิจ" in m
            or "คุณสมบัตินักศึกษา" in m
            or "ใครไปสหกิจได้" in m
            or "เงื่อนไขสหกิจ" in m
            or "สมัครสหกิจได้ไหม" in m
        ):
            return (
                "คุณสมบัตินักศึกษาสหกิจศึกษาโดยสรุป ได้แก่\n"
                "• ผ่านเงื่อนไขรายวิชาตามที่หลักสูตรกำหนด\n"
                "• มีคุณสมบัติครบตามที่คณะหรือหลักสูตรกำหนด\n"
                "• ไม่อยู่ระหว่างถูกลงโทษทางวินัย\n"
                "• เข้าร่วมกิจกรรมเตรียมความพร้อมก่อนปฏิบัติงานไม่น้อยกว่า 30 ชั่วโมง\n"
                "• มีความประพฤติเรียบร้อย\n"
                "• มีวุฒิภาวะทางอารมณ์และสามารถพัฒนาตนเองได้\n"
                "• มีคะแนนเฉลี่ยสะสมตั้งแต่ 2.50 ขึ้นไป"
            )

        # =========================
        # เกรดขั้นต่ำ
        # =========================
        if (
            "เกรดขั้นต่ำ" in m
            or "เกรด" in m
            or "เกรดเท่าไหร่" in m
            or "เกรดเฉลี่ย" in m
            or "gpax" in m
            or "gpa" in m
            or "เกรดไม่ถึง" in m
            or "2.50" in m
        ):
            return (
                "ตามคู่มือสหกิจศึกษา นักศึกษาต้องมีคะแนนเฉลี่ยสะสม "
                "(GPAX) ตั้งแต่ 2.50 ขึ้นไปครับ\n\n"
                "ทั้งนี้ ต้องผ่านเงื่อนไขรายวิชาและคุณสมบัติอื่น "
                "ตามที่คณะหรือหลักสูตรกำหนดด้วย"
            )

        # =========================
        # เตรียมความพร้อม / อบรม
        # =========================
        if (
            "เตรียมความพร้อม" in m
            or "อบรมกี่ชั่วโมง" in m
            or "อบรมสหกิจ" in m
            or "30 ชั่วโมง" in m
            or "ก่อนออกสหกิจ" in m
        ):
            return (
                "นักศึกษาต้องเข้าร่วมกิจกรรมเตรียมความพร้อมก่อนออกปฏิบัติงาน "
                "สหกิจศึกษาไม่น้อยกว่า 30 ชั่วโมงครับ"
            )

        # =========================
        # หัวข้ออบรมเตรียมความพร้อม
        # =========================
        if (
            "อบรมอะไรบ้าง" in m
            or "หัวข้ออบรม" in m
            or "เตรียมความพร้อมมีอะไรบ้าง" in m
        ):
            return (
                "หัวข้อเตรียมความพร้อมตามคู่มือ เช่น\n"
                "• ภาษาอังกฤษเพื่อการทำงาน\n"
                "• อาชีวอนามัยและความปลอดภัย\n"
                "• ระบบมาตรฐานสากล ISO\n"
                "• เทคนิคการนำเสนอและสถิติสำหรับนักศึกษา\n"
                "• การเจรจาต่อรองและกลยุทธ์การทำงาน\n"
                "• การพัฒนาบุคลิกภาพ\n"
                "• กฎหมายกับการทำงานครับ"
            )

        # =========================
        # สมัครงานสหกิจ
        # =========================
        if (
            "สมัครงานสหกิจ" in m
            or "สมัครสหกิจ" in m
            or "เลือกบริษัท" in m
            or "เลือกสถานประกอบการ" in m
            or "สมัครบริษัท" in m
        ):
            return (
                "นักศึกษาสามารถสมัครงานจากตำแหน่งที่สถานประกอบการเสนอ "
                "และมหาวิทยาลัยหรือคณะประกาศให้ทราบ โดยเลือกสมัครตามความสนใจ "
                "ครั้งละ 1 แห่ง หากไม่ได้รับการคัดเลือกจึงสามารถสมัครงานใหม่ได้ครับ"
            )

        # =========================
        # สมัครได้กี่แห่ง
        # =========================
        if (
            "สมัครได้กี่แห่ง" in m
            or "สมัครกี่บริษัท" in m
            or "สมัครพร้อมกัน" in m
        ):
            return (
                "ตามคู่มือ นักศึกษาสามารถสมัครงานได้ครั้งละ 1 แห่งครับ "
                "หากไม่ได้รับการคัดเลือกจึงสามารถสมัครงานใหม่ได้"
            )

        # =========================
        # ระยะเวลาปฏิบัติงาน
        # =========================
        if (
            "ฝึกกี่เดือน" in m
            or "สหกิจกี่เดือน" in m
            or "กี่สัปดาห์" in m
            or "ระยะเวลาสหกิจ" in m
            or "ระยะเวลาปฏิบัติงาน" in m
            or "16 สัปดาห์" in m
        ):
            return (
                "การปฏิบัติงานสหกิจศึกษาต้องมีระยะเวลาไม่น้อยกว่า "
                "16 สัปดาห์ และเป็นการปฏิบัติงานเต็มเวลา (Full Time) ครับ"
            )

        # =========================
        # ลักษณะงาน
        # =========================
        if (
            "ลักษณะงาน" in m
            or "ทำงานแบบไหน" in m
            or "งานสหกิจ" in m
            or "งานต้องตรงสาขาไหม" in m
            or "ตรงสาขา" in m
        ):
            return (
                "นักศึกษาสหกิจศึกษาปฏิบัติงานเสมือนเป็นพนักงานชั่วคราว "
                "ทำงานเต็มเวลา และมีหน้าที่รับผิดชอบงานที่แน่นอน "
                "ตรงตามสาขาวิชาชีพ โดยเน้นงานหรือโครงงานที่เป็นประโยชน์ "
                "ต่อสถานประกอบการครับ"
            )

        # =========================
        # เงินเดือน / เบี้ยเลี้ยง
        # =========================
        if (
            "เงินเดือน" in m
            or "เบี้ยเลี้ยง" in m
            or "ค่าตอบแทน" in m
            or "ได้เงินไหม" in m
            or "มีเงินไหม" in m
        ):
            return (
                "โดยปกติสถานประกอบการจะกำหนดค่าตอบแทนหรือเบี้ยเลี้ยงให้แก่นักศึกษา "
                "แต่บางหน่วยงานอาจมีค่าตอบแทนต่ำกว่า หรือไม่มีค่าตอบแทน "
                "ทั้งนี้ขึ้นอยู่กับสถานประกอบการครับ"
            )

        # =========================
        # สวัสดิการ
        # =========================
        if (
            "สวัสดิการ" in m
            or "ที่พัก" in m
            or "อาหาร" in m
            or "มีที่พักไหม" in m
        ):
            return (
                "สวัสดิการขึ้นอยู่กับสถานประกอบการครับ เช่น "
                "ค่าตอบแทน ที่พัก อาหาร หรือสวัสดิการอื่น ๆ "
                "หากสถานประกอบการจัดที่พักให้ ถือเป็นสวัสดิการเพิ่มเติม"
            )

        # =========================
        # ประกัน
        # =========================
        if (
            "ประกัน" in m
            or "ประกันอุบัติเหตุ" in m
            or "ประกันสุขภาพ" in m
        ):
            return (
                "นักศึกษาต้องทำประกันสุขภาพและอุบัติเหตุ "
                "เพื่อคุ้มครองการเจ็บป่วยและอุบัติเหตุที่อาจเกิดขึ้น "
                "ทั้งจากการปฏิบัติงานและการเดินทางตลอดระยะเวลาปฏิบัติงานครับ"
            )

        # =========================
        # สัปดาห์ที่ 1
        # =========================
        if (
            "สัปดาห์ที่ 1" in m
            or "อาทิตย์แรก" in m
            or "วันแรกสหกิจ" in m
            or "เริ่มฝึกต้องทำอะไร" in m
        ):
            return (
                "สัปดาห์ที่ 1 นักศึกษาต้องรายงานตัวเข้าปฏิบัติงาน "
                "ณ สถานประกอบการครับ"
            )

        # =========================
        # สัปดาห์ที่ 1-2
        # =========================
        if (
            "สัปดาห์ที่ 1-2" in m
            or "สัปดาห์ที่ 1 ถึง 2" in m
            or "วางแผน 16 สัปดาห์" in m
        ):
            return (
                "ในช่วงสัปดาห์ที่ 1–2 พนักงานพี่เลี้ยงของสถานประกอบการ "
                "และนักศึกษาจะร่วมกันวางแผนการปฏิบัติงาน 16 สัปดาห์ "
                "และกำหนดหัวข้อโครงงานครับ"
            )

        # =========================
        # นิเทศ
        # =========================
        if (
            "นิเทศ" in m
            or "อาจารย์นิเทศ" in m
            or "นิเทศตอนไหน" in m
            or "อาจารย์มาหา" in m
            or "เยี่ยมสถานประกอบการ" in m
        ):
            return (
                "โดยทั่วไปอาจารย์นิเทศจะนิเทศนักศึกษาระหว่างปฏิบัติงาน "
                "ประมาณสัปดาห์ที่ 5–12 และการนิเทศแต่ละครั้ง "
                "ใช้เวลาไม่น้อยกว่า 1 ชั่วโมงครับ"
            )

        # =========================
        # รายงานความก้าวหน้า
        # =========================
        if (
            "รายงานความก้าวหน้า" in m
            or "ความก้าวหน้า" in m
            or "รายงานกลางฝึก" in m
        ):
            return (
                "นักศึกษาต้องรายงานความก้าวหน้าต่อผู้นิเทศงาน "
                "และคณาจารย์นิเทศไม่ช้ากว่าสัปดาห์ที่ 10 "
                "ของการปฏิบัติงานสหกิจศึกษาครับ"
            )

        # =========================
        # บันทึกประจำวัน / สัปดาห์
        # =========================
        if (
            "บันทึกงาน" in m
            or "รายงานประจำวัน" in m
            or "รายงานประจำสัปดาห์" in m
            or "ต้องจดอะไร" in m
        ):
            return (
                "นักศึกษาต้องบันทึกรายงานการปฏิบัติงาน "
                "ประจำวันหรือประจำสัปดาห์ตลอดการปฏิบัติงานครับ"
            )

        # =========================
        # ระหว่างปฏิบัติงาน
        # =========================
        if (
            "ระหว่างฝึกต้องทำอะไร" in m
            or "ระหว่างสหกิจ" in m
            or "กิจกรรมนักศึกษา" in m
        ):
            return (
                "ระหว่างปฏิบัติงาน นักศึกษาต้อง\n"
                "• บันทึกรายงานประจำวันหรือประจำสัปดาห์\n"
                "• รายงานความก้าวหน้า\n"
                "• จัดทำรายงานสหกิจศึกษา\n"
                "• ส่งร่างรายงานให้ตรวจแก้\n"
                "• นำเสนอผลการปฏิบัติงานครับ"
            )

        # =========================
        # รายงานสหกิจ
        # =========================
        if (
            "รายงานสหกิจ" in m
            or "เขียนรายงาน" in m
            or "รายงานฉบับสมบูรณ์" in m
            or "ทำรายงาน" in m
        ):
            return (
                "รายงานสหกิจศึกษาฉบับสมบูรณ์เป็นรายงานทางวิชาการ "
                "ประกอบด้วยส่วนนำ ส่วนเนื้อเรื่อง และส่วนท้ายครับ\n\n"
                "เนื้อหาหลักประกอบด้วย\n"
                "• ข้อมูลสถานประกอบการ\n"
                "• ตำแหน่งและลักษณะงานที่ได้รับมอบหมาย\n"
                "• รายละเอียดงานหรือโครงงาน\n"
                "• ผลการปฏิบัติงาน\n"
                "• ข้อเสนอแนะ\n"
                "• บรรณานุกรมหรือเอกสารอ้างอิง\n"
                "• ภาคผนวก ถ้ามี"
            )

        # =========================
        # ส่งร่างรายงานเมื่อไหร่
        # =========================
        if (
            "ส่งร่างรายงาน" in m
            or "ร่างรายงานส่งตอนไหน" in m
        ):
            return (
                "ตามขั้นตอนในคู่มือ ช่วงสัปดาห์ที่ 13–15 "
                "นักศึกษาต้องส่งร่างรายงานให้พนักงานพี่เลี้ยงตรวจสอบและแก้ไขครับ"
            )

        # =========================
        # นำเสนอผลงาน
        # =========================
        if (
            "นำเสนอ" in m
            or "พรีเซนต์" in m
            or "presentation" in m
            or "นำเสนอผลงานตอนไหน" in m
        ):
            return (
                "ช่วงประมาณสัปดาห์ที่ 15 นักศึกษาจะนำเสนอผลการปฏิบัติงาน "
                "ต่อที่ประชุมในสถานประกอบการ และในช่วงสุดท้ายของสหกิจศึกษา "
                "ควรนำเสนอผลต่อผู้นิเทศงานและผู้บริหารสถานประกอบการด้วยครับ"
            )

        # =========================
        # สัปดาห์ที่ 16
        # =========================
        if (
            "สัปดาห์ที่ 16" in m
            or "อาทิตย์สุดท้าย" in m
            or "จบสหกิจ" in m
        ):
            return (
                "สัปดาห์ที่ 16 สถานประกอบการจะประเมินผลการปฏิบัติงาน "
                "และรายงานของนักศึกษาครับ"
            )

        # =========================
        # หลังกลับจากสถานประกอบการ
        # =========================
        if (
            "หลังกลับจากฝึก" in m
            or "หลังจบสหกิจ" in m
            or "กลับมหาลัยแล้วทำอะไร" in m
            or "ปัจฉิมนิเทศ" in m
        ):
            return (
                "หลังกลับจากสถานประกอบการ นักศึกษาต้องส่งรายงานฉบับสมบูรณ์ "
                "เข้าร่วมปัจฉิมนิเทศหรือกิจกรรมแลกเปลี่ยนประสบการณ์ "
                "และรับการประเมินผลจากหลักสูตรครับ"
            )

        # =========================
        # การประเมินผล
        # =========================
        if (
            "ประเมินผล" in m
            or "ให้คะแนนยังไง" in m
            or "คะแนนสหกิจ" in m
        ):
            return (
                "การประเมินผลสหกิจศึกษาครอบคลุมทั้งก่อน ระหว่าง "
                "และหลังการปฏิบัติงานครับ โดยการประเมินจากสถานประกอบการ "
                "ต้องมีสัดส่วนไม่น้อยกว่าร้อยละ 50"
            )

        # =========================
        # เกณฑ์การประเมิน
        # =========================
        if (
            "ประเมินอะไรบ้าง" in m
            or "เกณฑ์ประเมิน" in m
            or "หัวข้อประเมิน" in m
        ):
            return (
                "หัวข้อประเมินสำคัญ เช่น\n"
                "• ปริมาณและคุณภาพงาน\n"
                "• ความรู้ความสามารถทางวิชาการ\n"
                "• การเรียนรู้และประยุกต์ใช้ความรู้\n"
                "• การวางแผนและการตัดสินใจ\n"
                "• ทักษะการสื่อสาร\n"
                "• ความรับผิดชอบ\n"
                "• ความสนใจและความตั้งใจในการทำงาน\n"
                "• การทำงานร่วมกับผู้อื่น\n"
                "• ระเบียบวินัย\n"
                "• คุณธรรมและจริยธรรมครับ"
            )

        # =========================
        # ประโยชน์ของสหกิจ
        # =========================
        if (
            "ประโยชน์สหกิจ" in m
            or "สหกิจมีประโยชน์อะไร" in m
            or "ข้อดีสหกิจ" in m
        ):
            return (
                "ประโยชน์ของสหกิจศึกษาสำหรับนักศึกษา เช่น\n"
                "• ได้รับประสบการณ์วิชาชีพจริง\n"
                "• พัฒนาการทำงานร่วมกับผู้อื่นและความรับผิดชอบ\n"
                "• พัฒนาทักษะการสื่อสาร\n"
                "• ได้รู้จักความถนัดและสายอาชีพของตนเองมากขึ้น\n"
                "• มีความพร้อมในการทำงานหลังจบการศึกษามากขึ้นครับ"
            )

        # =========================
        # พนักงานพี่เลี้ยง / Job Supervisor
        # =========================
        if (
            "พี่เลี้ยง" in m
            or "job supervisor" in m
            or "ผู้นิเทศงาน" in m
            or "พนักงานที่ปรึกษา" in m
        ):
            return (
                "พนักงานที่ปรึกษาหรือ Job Supervisor คือบุคลากรของสถานประกอบการ "
                "ที่ได้รับมอบหมายให้ดูแล ให้คำปรึกษา ติดตามการปฏิบัติงาน "
                "ตรวจรายงาน และประเมินผลการทำงานของนักศึกษาครับ"
            )

        # =========================
        # สมัครสมาชิก CoopHub
        # =========================
        # =========================
        # สมัครสมาชิก CoopHub
        # =========================
        if "สมัครสมาชิก" in m or "register" in m:
            return (
                "การสมัครสมาชิก CoopHub: ไปที่หน้า Register "
                "แล้วกรอกข้อมูลให้ครบ จากนั้นดำเนินการยืนยันบัญชีตามขั้นตอนของระบบครับ"
            )

        # =========================
        # วิธีสมัครสหกิจศึกษา
        # =========================
        if (
            "วิธีสมัคร" in m
            or "สมัครยังไง" in m
            or "สมัครอย่างไร" in m
            or "ขั้นตอนการสมัคร" in m
            or "สมัครสหกิจยังไง" in m
            or "สมัครงานสหกิจยังไง" in m
        ):
            return (
                "วิธีสมัครสหกิจศึกษาโดยสรุปครับ\n"
                "1. ตรวจสอบว่าตนเองมีคุณสมบัติตามที่คณะหรือหลักสูตรกำหนด\n"
                "2. เลือกตำแหน่งงานหรือสถานประกอบการที่มหาวิทยาลัย/คณะประกาศ\n"
                "3. นักศึกษาสมัครงานได้ครั้งละ 1 แห่ง\n"
                "4. สถานประกอบการพิจารณาใบสมัคร และอาจมีการสัมภาษณ์\n"
                "5. หากไม่ได้รับการคัดเลือก สามารถสมัครสถานประกอบการแห่งใหม่ได้\n"
                "6. เมื่อได้รับการคัดเลือก มหาวิทยาลัย/คณะจะประกาศผลก่อนออกปฏิบัติงาน\n\n"
                "ควรเลือกสถานประกอบการและลักษณะงานที่ตรงกับความสนใจ "
                "และความถนัดของตนเองเป็นหลักครับ"
            )

        # =========================
        # สร้างโพสต์ CoopHub
        # =========================
        if (
            "สร้างโพสต์" in m
            or "ลงประกาศ" in m
            or "โพสต์ฝึกงาน" in m
        ):
            return (
                "การสร้างโพสต์ฝึกงานใน CoopHub ให้กดเมนู 'สร้างโพสต์' "
                "แล้วกรอกข้อมูลสถานประกอบการ ตำแหน่งงาน รูปแบบการฝึก "
                "วันทำงาน ค่าตอบแทน สวัสดิการ และข้อมูลที่เกี่ยวข้องให้ครบครับ"
            )

        # =========================
        # คู่มือสหกิจศึกษา
        # =========================
        if (
            "คู่มือ" in m
            or "ขอคู่มือ" in m
            or "คู่มือสหกิจ" in m
            or "คู่มือสหกิจศึกษา" in m
            or "ไฟล์คู่มือ" in m
            or "เอกสารสหกิจ" in m
        ):
            return (
                "📘 คู่มือสหกิจศึกษา\n\n"
                "สามารถเปิดคู่มือได้ที่นี่ครับ\n"
                "/media/documents/cooperative_education_manual.pdf"
            )

        # =========================
        # ไม่พบคำตอบ
        # ต้องอยู่ล่างสุดเสมอ
        # =========================
        return (
            "คำถามนี้ผมยังตอบไม่ได้ครับ 🙏\n"
            "ลองถามเกี่ยวกับคุณสมบัติสหกิจ เกรดขั้นต่ำ การสมัคร "
            "ระยะเวลาปฏิบัติงาน การนิเทศ รายงาน "
            "ค่าตอบแทน หรือสวัสดิการได้ครับ\n\n"
            "หากเป็นข้อมูลเฉพาะของสาขาวิชา "
            "กรุณาสอบถามอาจารย์หรือแอดมินครับ"
        )