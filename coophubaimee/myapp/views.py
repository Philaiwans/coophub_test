# myapp/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.urls import reverse
from django.contrib.auth.decorators import login_required   # ✅ สำคัญ!
import re

from .models import CustomUser
from .tokens import account_activation_token


def home_redirect(request):
    return redirect('login')

def register(request):
    if request.method == 'POST':
        email = request.POST['email'].strip()
        username = request.POST['username'].strip()
        password = request.POST['password']
        confirm = request.POST['confirm']
        role = request.POST['role']
        student_id = request.POST.get('student_id', '').strip()

        if password != confirm:
            messages.error(request, 'รหัสผ่านไม่ตรงกัน')
            return redirect('register')

        if role == 'student' and not re.match(r'.+@ubu\.ac\.th$', email, re.IGNORECASE):
            messages.error(request, 'กรุณาใช้อีเมลมหาวิทยาลัย (@ubu.ac.th)')
            return redirect('register')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'ชื่อผู้ใช้นี้ถูกใช้แล้ว')
            return redirect('register')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'อีเมลนี้ถูกใช้ไปแล้ว')
            return redirect('register')

        # ✅ สร้างผู้ใช้ใหม่
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            student_id=student_id,
            is_active=False,
        )

        # ✅ ตั้งค่าพิเศษแยกตาม role
        if role == 'teacher':
            user.approved = False
        else:
            user.approved = True

        user.save()

        # ✅ ส่งอีเมลยืนยัน
        current_site = get_current_site(request)
        mail_subject = 'ยืนยันอีเมลเพื่อเปิดใช้งานบัญชี CoopHub'
        message = render_to_string('email_verification.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        EmailMessage(mail_subject, message, to=[email]).send()

        messages.success(request, 'สมัครสำเร็จ! กรุณาตรวจอีเมลเพื่อยืนยันบัญชีก่อนเข้าสู่ระบบ')
        return redirect('login')

    return render(request, 'register.html')


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'ยืนยันอีเมลเรียบร้อยแล้ว! กรุณาเข้าสู่ระบบ')
        return redirect('login')
    else:
        messages.error(request, 'ลิงก์ยืนยันไม่ถูกต้องหรือหมดอายุ')
        return redirect('register')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username'].strip()
        password = request.POST['password']

        # ช่องทางพิเศษ: แอดมินฟิกค่าบัญชี
        if username == 'admin007' and password == 'admin007x':
            user = authenticate(request, username=username, password=password)
            if user is None:
                # เผื่อยังไม่ได้สร้าง superuser: แจ้งผู้ใช้ไปสร้างก่อน
                messages.error(request, 'ยังไม่มีผู้ใช้ admin007 ในฐานข้อมูล กรุณาสร้าง superuser ก่อน')
                return redirect('login')
            login(request, user)
            return redirect('admin_dashboard')

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
            return redirect('login')

        if not user.is_active:
            messages.error(request, 'บัญชียังไม่ถูกยืนยันอีเมล')
            return redirect('login')

        if user.role == 'teacher' and not user.approved:
            messages.error(request, 'บัญชีอาจารย์กำลังรอการอนุมัติจากแอดมิน')
            return redirect('login')

        login(request, user)
        if user.role == 'student':
            return redirect('student_home')
        elif user.role == 'teacher':
            return redirect('teacher_home')
        else:
            return redirect('admin_dashboard')

    return render(request, 'login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def student_home(request):
    if request.user.role != 'student':
        return redirect('login')
    return render(request, 'student_home.html', {'user_obj': request.user})


@login_required
def teacher_home(request):
    if request.user.role != 'teacher':
        return redirect('login')
    return render(request, 'teacher_home.html', {'user_obj': request.user})


@login_required
def admin_dashboard(request):
    if request.user.role != 'admin' and request.user.username != 'admin007':
        return redirect('login')

    # รายชื่ออาจารย์ที่รออนุมัติ
    pending_teachers = CustomUser.objects.filter(role='teacher', approved=False, is_active=True)

    # กดอนุมัติผ่าน querystring ?approve=<id>
    approve_id = request.GET.get('approve')
    if approve_id:
        try:
            t = CustomUser.objects.get(id=approve_id, role='teacher')
            t.approved = True
            t.save()
            messages.success(request, f'อนุมัติ {t.username} แล้ว')
            return redirect('admin_dashboard')
        except CustomUser.DoesNotExist:
            messages.error(request, 'ไม่พบผู้ใช้อาจารย์ที่ต้องการอนุมัติ')

    return render(request, 'admin_dashboard.html', {'pending_teachers': pending_teachers})
