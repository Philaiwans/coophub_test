import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import CoopPost, Comment, Notification


class CommentConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.post_id = self.scope["url_route"]["kwargs"]["post_id"]
        self.room_group_name = f"post_comments_{self.post_id}"

        user = self.scope["user"]

        if not user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )


    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        message = data.get("message", "").strip()

        if not message:
            return

        user = self.scope["user"]

        if not user.is_authenticated:
            return

        comment_data = await self.create_comment(
            user=user,
            post_id=self.post_id,
            message=message
        )

        if not comment_data:
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "comment_message",

                "comment_id": comment_data["id"],
                "message": comment_data["message"],

                "user_id": user.id,
                "first_name": user.first_name or user.username,
                "last_name": user.last_name or "",
                "role": user.role,

                "student_id": getattr(
                    user,
                    "student_id",
                    ""
                ) or "",

                "profile_image": comment_data["profile_image"],
                "created_at": comment_data["created_at"],
            }
        )


    async def comment_message(self, event):
        await self.send(
            text_data=json.dumps({
                "comment_id": event["comment_id"],
                "message": event["message"],

                "user_id": event["user_id"],
                "first_name": event["first_name"],
                "last_name": event["last_name"],

                "role": event["role"],
                "student_id": event["student_id"],

                "profile_image": event["profile_image"],
                "created_at": event["created_at"],
            })
        )


    @database_sync_to_async
    def create_comment(self, user, post_id, message):

        try:
            post = CoopPost.objects.select_related("owner").get(
                id=post_id
            )

        except CoopPost.DoesNotExist:
            return None


        comment = Comment.objects.create(
            post=post,
            user=user,
            text=message
        )


        # =========================
        # แจ้งเตือนเจ้าของโพสต์
        # =========================

        if post.owner_id != user.id:

            display_name = (
                f"{user.first_name} {user.last_name}".strip()
                or user.username
            )

            Notification.objects.create(
                user=post.owner,
                actor=user,
                post=post,
                comment=comment,
                noti_type="comment",
                message=f"{display_name} แสดงความคิดเห็นในโพสต์ {post.company}"
            )


        # =========================
        # รูปโปรไฟล์
        # =========================

        profile_image = ""

        if user.profile_image:
            try:
                profile_image = user.profile_image.url
            except ValueError:
                profile_image = ""


        return {
            "id": comment.id,
            "message": comment.text,
            "profile_image": profile_image,
            "created_at": comment.created_at.strftime(
                "%d/%m/%Y %H:%M"
            ),
        }