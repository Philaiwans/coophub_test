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
    salary = models.CharField(max_length=50)
    company = models.CharField(max_length=255)
    province = models.CharField(max_length=255)
    salary = models.CharField(max_length=50)
    position = models.CharField(max_length=255)
    work_time = models.CharField(max_length=255)
    internship_period = models.CharField(max_length=255)
    location = models.TextField()
    skills = models.TextField()
    grade = models.CharField(max_length=20)
    contact = models.CharField(max_length=255)
    type_of_work = models.CharField(max_length=255)
    portfolio = models.URLField(blank=True, null=True)
    extra_link = models.URLField(blank=True, null=True)
    extra_file = models.FileField(upload_to='extra_files/', blank=True, null=True)

    description = models.TextField()
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    
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


# ---------- ความคิดเห็น ----------
class Comment(models.Model):
    post = models.ForeignKey(CoopPost, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


