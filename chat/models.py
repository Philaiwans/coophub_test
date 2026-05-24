# chat/models.py
from django.db import models
from django.conf import settings
from django.utils.text import slugify 

class Room(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, blank=True) # ให้ slug เป็น blank=True, unique=True
    
    # ⭐ เพิ่มฟิลด์สำหรับแยกประเภทห้อง
    is_major_chat = models.BooleanField(default=False)
    major_name = models.CharField(max_length=255, blank=True, null=True, unique=True) # สำหรับ Major Chat
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f'{self.user.username}: {self.content[:50]}'
    
    # chat/models.py
from django.db import models
from django.conf import settings

class Room(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    is_major_chat = models.BooleanField(default=False)
    major_name = models.CharField(max_length=255, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Message(models.Model):
    TYPE_CHOICES = (
        ("text", "Text"),
        ("image", "Image"),
        ("file", "File"),
        ("link", "Link"),
    )

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="messages")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    message_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="text")
    content = models.TextField(blank=True)  # text หรือ caption
    attachment_url = models.URLField(blank=True, null=True)  # url รูป/ไฟล์
    attachment_name = models.CharField(max_length=255, blank=True, null=True)  # ชื่อไฟล์แสดงผล

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.user.username}: {self.content[:50]}"
