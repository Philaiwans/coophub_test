#models.py/myapp
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'นักศึกษา'),
        ('teacher', 'อาจารย์'),
        ('admin', 'แอดมิน'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    student_id = models.CharField(max_length=20, blank=True, null=True)
    approved = models.BooleanField(default=False)

    faculty = models.CharField(max_length=255, blank=True, null=True)
    major = models.CharField(max_length=255, blank=True, null=True)

    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# ---------- โพสต์ ----------
class CoopPost(models.Model):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    # ข้อมูลหลัก
    company = models.CharField(max_length=255)
    province = models.CharField(max_length=255)
    salary = models.CharField(max_length=50)          # เช่น "300 บาท", "ตามตกลง"
    position = models.CharField(max_length=255)       # เก็บหลายตำแหน่งแบบ "Frontend, Backend"
    work_time = models.CharField(max_length=255)      # "จันทร์-ศุกร์ 09:00 - 17:00"
    internship_period = models.CharField(max_length=255)  # "2025-01-01 ถึง 2025-05-31"

    # ที่ตั้ง + เช็คอิน
    location = models.TextField()
    checkin_location = models.CharField(              # ⭐ ลิงก์หรือข้อมูลเช็คอิน
        max_length=255,
        blank=True,
        null=True,
        help_text="ลิงก์ Google Maps หรือข้อความสำหรับเช็คอิน"
    )

    # ทักษะ/คุณสมบัติ
    skills = models.TextField()
    grade = models.CharField(max_length=20, blank=True, null=True)
    contact = models.CharField(max_length=255)
    type_of_work = models.CharField(max_length=255)   # On-site / Online / Hybrid

    # ลิงก์ / ไฟล์ประกอบ
    portfolio = models.URLField(blank=True, null=True)
    extra_link = models.URLField(blank=True, null=True)
    extra_file = models.FileField(upload_to='extra_files/', blank=True, null=True)
    video = models.FileField(upload_to='post_videos/', blank=True, null=True)  # ⭐ วิดีโอ

    # เนื้อหา / รูปปก
    description = models.TextField()
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)

    # สถานะโพสต์
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'รออนุมัติ'),
            ('approved', 'ผ่าน'),
            ('rejected', 'ไม่ผ่าน'),
            ('deleted', 'ลบแล้ว'),
        ],
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company} - {self.owner.username}"


# ---------- รูปภาพประกอบเพิ่มเติม ----------
class CoopPostImage(models.Model):
    post = models.ForeignKey(
        CoopPost,
        on_delete=models.CASCADE,
        related_name='extra_images'   # เรียกใช้ได้ด้วย post.extra_images.all()
    )
    image = models.ImageField(upload_to='post_extra_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Extra image for {self.post.company}"


# ---------- ความคิดเห็น ----------
class Comment(models.Model):
    post = models.ForeignKey(CoopPost, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.company}"


class Bookmark(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    post = models.ForeignKey(CoopPost, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')   # 1 user bookmark 1 post ได้ครั้งเดียว
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} -> {self.post.company}"
class PostView(models.Model):
    post = models.ForeignKey(
        CoopPost,
        on_delete=models.CASCADE,
        related_name='views'
    )
    # ถ้า user ไม่ล็อกอิน (เผื่อใช้ในอนาคต) ให้เป็น null ได้
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        uname = self.user.username if self.user else "anonymous"
        return f"View {self.post.id} by {uname}"


# ---------- การแจ้งเตือน ----------
class Notification(models.Model):
    NOTI_TYPE_CHOICES = (
        ('post', 'โพสต์ใหม่/อัปเดตโพสต์'),      # แท็บ "แจ้งเตือน"
        ('comment', 'ความคิดเห็น'),             # แท็บ "ความคิดเห็น"
        ('review', 'ตรวจสอบโพสต์'),             # แท็บ "ตรวจสอบ"
        ('approval', 'ประวัติการอนุมัติ'),      # แท็บ "การอนุมัติ"
    )

    # คนที่ "ได้รับ" การแจ้งเตือน
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    # คนที่เป็น "ผู้กระทำ" เช่น คนคอมเมนต์ / คนสร้างโพสต์ / คนอนุมัติ
    actor = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actor_notifications'
    )

    post = models.ForeignKey(
        CoopPost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # ใช้ string 'Comment' เพราะอยู่ล่างกว่าในไฟล์
    comment = models.ForeignKey(
        'Comment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    noti_type = models.CharField(max_length=20, choices=NOTI_TYPE_CHOICES)
    message = models.TextField()

    # ใช้เก็บผลการอนุมัติ เช่น approved / rejected
    extra_status = models.CharField(max_length=20, blank=True, null=True)

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.noti_type}"
