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

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
