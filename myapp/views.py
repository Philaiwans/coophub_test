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
from django.contrib.auth.decorators import login_required
import re
from django.db.models import Q
from .models import CustomUser
from .tokens import account_activation_token
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import CoopPost
from django.db import models
def home_redirect(request):
    return redirect('login')
from chat.models import Room
from django.utils.text import slugify

def register(request):
    if request.method == 'POST':
        first_name = request.POST['first_name'].strip()
        last_name = request.POST['last_name'].strip()
        email = request.POST['email'].strip()
        username = request.POST['username'].strip()
        password = request.POST['password']
        confirm = request.POST['confirm']
        role = request.POST['role']
        student_id = request.POST.get('student_id', '').strip()
        faculty = request.POST.get('faculty', '').strip()
        major = request.POST.get('major', '').strip()

        if password != confirm:
            messages.error(request, 'รหัสผ่านไม่ตรงกัน')
            return redirect('register')

        #if role == 'student' and not re.match(r'.+@ubu\.ac\.th$', email, re.IGNORECASE):
           # messages.error(request, 'กรุณาใช้อีเมลมหาวิทยาลัย (@ubu.ac.th)')
            #return redirect('register')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'ชื่อผู้ใช้นี้ถูกใช้แล้ว')
            return redirect('register')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'อีเมลนี้ถูกใช้ไปแล้ว')
            return redirect('register')

        # สร้างผู้ใช้ใหม่
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            student_id=student_id,
            faculty=faculty,
            major=major,
            first_name=first_name,
            last_name=last_name,
            is_active=False,
        )

        # การอนุมัติอาจารย์
        if role == 'teacher':
            user.approved = False
        else:
            user.approved = True

        user.save()

#chat
def register(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        confirm = request.POST.get("confirm", "")
        role = request.POST.get("role", "")
        student_id = request.POST.get("student_id", "").strip()
        faculty = request.POST.get("faculty", "").strip()
        major = request.POST.get("major", "").strip()

        if password != confirm:
            messages.error(request, "รหัสผ่านไม่ตรงกัน")
            return redirect("register")

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "ชื่อผู้ใช้นี้ถูกใช้แล้ว")
            return redirect("register")

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "อีเมลนี้ถูกใช้ไปแล้ว")
            return redirect("register")

        # ✅ สร้างผู้ใช้ใหม่ (ต้องมี user ก่อนใช้งานเสมอ)
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            student_id=student_id,
            faculty=faculty,
            major=major,
            first_name=first_name,
            last_name=last_name,
            is_active=False,
        )

        # การอนุมัติอาจารย์
        user.approved = (role != "teacher")
        user.save()

        # ✅ สร้างห้องแชท
        Room.objects.get_or_create(
            slug="coophub-community",
            defaults={"name": "CoopHub Community"}
        )

        if major:
            Room.objects.get_or_create(
                slug=f"major-{slugify(major)}",
                defaults={"name": f"Major Chat - {major}"}
            )

        Room.objects.get_or_create(
            slug=f"chatbot-{role}".lower(),
            defaults={"name": f"Chatbot ({role})"}
        )

        # ✅ ส่งอีเมลยืนยัน
        current_site = get_current_site(request)
        mail_subject = "ยืนยันอีเมลเพื่อเปิดใช้งานบัญชี CoopHub"

        message = render_to_string("email_verification.html", {
            "user": user,
            "domain": current_site.domain,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": account_activation_token.make_token(user),
        })

        email_message = EmailMessage(mail_subject, message, to=[email])
        email_message.content_subtype = "html"
        email_message.send()

        messages.success(request, "สมัครสำเร็จ! กรุณาตรวจอีเมลเพื่อยืนยันบัญชีก่อนเข้าสู่ระบบ")
        return redirect("login")

    return render(request, "register.html")



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

        if username == 'admin007' and password == 'admin007x':
            user = authenticate(request, username=username, password=password)
            if user is None:
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

    # -----------------------------
    # 1) ฟีเจอร์อนุมัติอาจารย์
    # -----------------------------
    pending_teachers = CustomUser.objects.filter(
        role='teacher',
        approved=False,
        is_active=True
    )

    approve_id = request.GET.get('approve')
    if approve_id:
        try:
            t = CustomUser.objects.get(id=approve_id, role='teacher')
            t.approved = True
            t.save()
            messages.success(request, f"อนุมัติ {t.first_name} {t.last_name} สำเร็จ")
            return redirect('admin_dashboard')
        except CustomUser.DoesNotExist:
            messages.error(request, "ไม่พบอาจารย์")

    # -----------------------------
    # 2) ดึงโพสต์ทั้งหมดเพื่อแสดงในฟีด
    # -----------------------------
    search = request.GET.get("search", "").strip()

    posts = CoopPost.objects.filter(status__in=["approved", "expired"])

    if search:
        posts = posts.filter(
            Q(company__icontains=search) |
            Q(position__icontains=search) |
            Q(province__icontains=search) |
            Q(owner__first_name__icontains=search) |
            Q(owner__last_name__icontains=search)
        )

    posts = posts.order_by('-created_at')

    # -----------------------------
    # ส่งไปยัง Template
    # -----------------------------
    return render(request, 'admin_dashboard.html', {
        "user_obj": request.user,
        "posts": posts,
        "pending_teachers": pending_teachers,
        "search": search,
    })




@login_required
def profile_view(request):
    return render(request, 'profile.html', {'user': request.user})


# myapp/views.py
@login_required
def edit_profile(request):
    user = request.user

    if request.method == "POST":
        # อนุญาตให้แก้ไขพวกข้อมูลทั่วไป
        user.username = request.POST.get("username", user.username).strip()
        user.first_name = request.POST.get("first_name", user.first_name).strip()
        user.last_name = request.POST.get("last_name", user.last_name).strip()
        user.faculty = request.POST.get("faculty", user.faculty).strip()
        user.major = request.POST.get("major", user.major).strip()

        # เฉพาะ student เท่านั้นที่มีรหัสนักศึกษา
        if user.role == "student":
            user.student_id = request.POST.get("student_id", user.student_id).strip()

        # ❌ ไม่อนุญาตให้แก้ email จากหน้านี้ (จะใช้ระบบเปลี่ยนรหัสผ่านแทน)
        # ข้าม user.email ไปเลย

        # อัปโหลดรูปโปรไฟล์
        if request.FILES.get("profile_image"):
            user.profile_image = request.FILES["profile_image"]

        user.save()
        messages.success(request, "อัปเดตข้อมูลเรียบร้อยแล้ว")
        return redirect("profile")

    return render(request, "edit_profile.html", {"user": user})



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import (
    CoopPost, Comment, CustomUser,
    CoopPostImage, Bookmark, Notification,
    PostView,
)




from django.db.models import Q   # 👈 เพิ่มบรรทัดนี้ด้านบนของ views.py

@login_required
def student_home(request):
    if request.user.role != 'student':
        return redirect('login')

    search = request.GET.get("search", "").strip()

    posts = CoopPost.objects.filter(status="approved")

    if search:
        posts = posts.filter(
            Q(company__icontains=search) |
            Q(position__icontains=search) |
            Q(province__icontains=search) |
            Q(owner__first_name__icontains=search) |
            Q(owner__last_name__icontains=search)
        )

    posts = posts.order_by('-created_at')

    # ✅ ดึง post ที่ user คนนี้ bookmark ไว้
    bookmarked_ids = set(
        Bookmark.objects.filter(user=request.user).values_list('post_id', flat=True)
    )

    return render(request, 'student_home.html', {
        "user_obj": request.user,
        "posts": posts,
        "search": search,
        "bookmarked_ids": bookmarked_ids,   # ส่งไป template
    })


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


# ---------- รายชื่อจังหวัด 77 จังหวัด + ต่างประเทศ ----------
PROVINCES = [
    "กรุงเทพมหานคร","กระบี่","กาญจนบุรี","กาฬสินธุ์","กำแพงเพชร","ขอนแก่น",
    "จันทบุรี","ฉะเชิงเทรา","ชลบุรี","ชัยนาท","ชัยภูมิ","ชุมพร","เชียงราย","เชียงใหม่",
    "ตรัง","ตราด","ตาก","นครนายก","นครปฐม","นครพนม","นครราชสีมา","นครศรีธรรมราช",
    "นครสวรรค์","นนทบุรี","นราธิวาส","น่าน","บึงกาฬ","บุรีรัมย์","ปทุมธานี","ประจวบคีรีขันธ์",
    "ปราจีนบุรี","ปัตตานี","พระนครศรีอยุธยา","พะเยา","พังงา","พัทลุง","พิจิตร","พิษณุโลก",
    "เพชรบุรี","เพชรบูรณ์","แพร่","ภูเก็ต","มหาสารคาม","มุกดาหาร","ยะลา","ยโสธร","ร้อยเอ็ด",
    "ระนอง","ระยอง","ราชบุรี","ลพบุรี","ลำปาง","ลำพูน","เลย","ศรีสะเกษ","สกลนคร","สงขลา",
    "สตูล","สมุทรปราการ","สมุทรสงคราม","สมุทรสาคร","สระบุรี","สระแก้ว","สุพรรณบุรี",
    "สุราษฎร์ธานี","สุรินทร์","สุโขทัย","หนองคาย","หนองบัวลำภู","อ่างทอง","อุดรธานี",
    "อุตรดิตถ์","อุทัยธานี","อุบลราชธานี",
    "ต่างประเทศ",
]


# ---------- ฟังก์ชันสร้างโพสต์ ----------
@login_required
def create_post(request):

    if request.method == "POST":

        work_time = f"{request.POST.get('work_day')} {request.POST.get('time_start')} - {request.POST.get('time_end')}"
        internship_period = f"{request.POST.get('start_date')} ถึง {request.POST.get('end_date')}"

        salary_type = request.POST.get('salary_type')
        salary_amount = request.POST.get('salary_amount')

        if salary_type == "มี" and salary_amount:
            salary = f"{salary_amount} บาท"
        else:
            salary = salary_type

        positions_list = request.POST.getlist('positions[]')
        positions_list = [p.strip() for p in positions_list if p.strip()]
        positions_str = ", ".join(positions_list)

        portfolio = request.POST.get("portfolio") or ""
        extra_link = request.POST.get("extra_link") or ""
        checkin_location = request.POST.get("checkin_location") or ""

        post = CoopPost(
            owner=request.user,
            company=request.POST.get('company'),
            province=request.POST.get('province'),
            salary=salary,
            position=positions_str,
            work_time=work_time,
            internship_period=internship_period,
            location=request.POST.get('location'),
            checkin_location=checkin_location,
            skills=request.POST.get('skills'),
            grade=request.POST.get('grade'),
            contact=request.POST.get('contact'),
            type_of_work=request.POST.get('type_of_work'),
            description=request.POST.get('description'),
            portfolio=portfolio,
            extra_link=extra_link,
        )

        if request.FILES.get('image'):
            post.image = request.FILES['image']

        if request.FILES.get('extra_file'):
            post.extra_file = request.FILES['extra_file']

        if request.FILES.get('extra_video'):
            post.video = request.FILES['extra_video']

        # ---------------- สถานะโพสต์ ----------------
        if request.user.role in ['teacher', 'admin'] or request.user.username == 'admin007':
            # ครู/แอดมินโพสต์เอง = ผ่านเลย
            post.status = "approved"
        else:
            # นักศึกษา = รอตรวจสอบ
            post.status = "pending"

        post.save()

        # รูปประกอบหลายรูป
        extra_images = request.FILES.getlist('extra_images')
        for img in extra_images:
            CoopPostImage.objects.create(post=post, image=img)

        # =============== NOTIFICATION ===============

        # 1) ถ้าเป็นนักศึกษา → ส่ง "ตรวจสอบ" ให้ครูสาขาเดียวกัน + แอดมิน
        if request.user.role == 'student':
            teachers = CustomUser.objects.filter(
                role='teacher',
                major=request.user.major,
                approved=True,
                is_active=True
            )
            admins = CustomUser.objects.filter(
                Q(role='admin') | Q(username='admin007'),
                is_active=True
            )

            for receiver in list(teachers) + list(admins):
                Notification.objects.create(
                    user=receiver,
                    actor=request.user,
                    post=post,
                    noti_type='review',   # ← ใช้สำหรับแท็บ "ตรวจสอบ"
                    message=f"{request.user.first_name} สร้างโพสต์ใหม่ให้คุณช่วยตรวจสอบ"
                )

            for receiver in list(teachers) + list(admins):
                Notification.objects.create(
                    user=receiver,
                    actor=request.user,
                    post=post,
                    noti_type='review',
                    message=f"{request.user.first_name} สร้างโพสต์ใหม่ให้คุณช่วยตรวจสอบ"
                )

        # 2) ถ้าเป็นครู/แอดมินโพสต์เอง (status=approved) → แจ้งเตือนโพสต์ใหม่ให้ครู/แอดมินคนอื่น (แท็บ 'แจ้งเตือน')
        if post.status == "approved":
            receivers = CustomUser.objects.filter(
                models.Q(role='teacher') | models.Q(role='admin') | models.Q(username='admin007'),
                is_active=True
            ).exclude(id=request.user.id)

            for receiver in receivers:
                Notification.objects.create(
                    user=receiver,
                    actor=request.user,
                    post=post,
                    noti_type='post',
                    message=f"{request.user.first_name} โพสต์สถานที่ฝึกงานใหม่: {post.company}"
                )
        # ============================================

        return redirect("post_success")

    return render(request, 'post_create.html', {
        "provinces": PROVINCES
    })



# views.py
from django.db.models import Q

# ถ้ายังไม่มีให้ประกาศไว้สักที่ (คุณมีอยู่แล้วในไฟล์)
# POSITION_CHOICES = [...]

@login_required
def teacher_home(request):
    if request.user.role != 'teacher':
        return redirect('login')

    # --------- รับค่า filter จาก GET ----------
    search = request.GET.get("search", "").strip()
    order = request.GET.get("order", "new")              # new | old
    poster = request.GET.get("poster", "all")            # all | student | teacher | admin
    province = request.GET.get("province", "all")        # all | <จังหวัด>
    work_type = request.GET.get("work_type", "all")      # all | <type_of_work>
    position = request.GET.get("position", "all")        # all | <ตำแหน่ง>
    salary_kind = request.GET.get("salary_kind", "all")  # all | paid | none | negotiable

    # --------- queryset หลัก ----------
    posts = CoopPost.objects.filter(status__in=["approved", "expired"]).select_related("owner")

    # --------- search ----------
    if search:
        posts = posts.filter(
            Q(company__icontains=search) |
            Q(position__icontains=search) |
            Q(province__icontains=search) |
            Q(owner__first_name__icontains=search) |
            Q(owner__last_name__icontains=search)
        )

    # --------- filter: poster ----------
    if poster != "all":
        posts = posts.filter(owner__role=poster)

    # --------- filter: province ----------
    if province != "all":
        posts = posts.filter(province=province)

    # --------- filter: work_type ----------
    if work_type != "all":
        posts = posts.filter(type_of_work=work_type)

    # --------- filter: position (ใน DB เก็บแบบ "A, B, C") ----------
    if position != "all":
        posts = posts.filter(position__icontains=position)

    # --------- filter: salary_kind (salary เป็นข้อความ เช่น "300 บาท", "ตามตกลง", "ไม่มี") ----------
    if salary_kind == "paid":
        posts = posts.filter(salary__icontains="บาท")
    elif salary_kind == "none":
        posts = posts.filter(salary__icontains="ไม่มี")
    elif salary_kind == "negotiable":
        posts = posts.filter(salary__icontains="ตามตกลง")

    # --------- ordering ----------
    if order == "old":
        posts = posts.order_by("created_at")
    else:
        posts = posts.order_by("-created_at")

    # --------- ตัวเลือกสำหรับ dropdown ----------
    # จังหวัด: ใช้ PROVINCES ที่คุณประกาศไว้
    provinces = PROVINCES

    # รูปแบบการฝึก: ดึงจากโพสต์ที่มีจริง (ไม่ต้อง hardcode)
    work_type_choices = (
        CoopPost.objects.filter(status__in=["approved", "expired"])
        .exclude(type_of_work__isnull=True)
        .exclude(type_of_work__exact="")
        .values_list("type_of_work", flat=True)
        .distinct()
        .order_by("type_of_work")
    )

    # ตำแหน่ง: ใช้ลิสต์ POSITION_CHOICES ที่คุณมี
    position_choices = POSITION_CHOICES

    return render(request, 'teacher_home.html', {
        "user_obj": request.user,
        "posts": posts,

        # ค่า search/filter ส่งกลับไปให้ template select ถูกช่อง
        "search": search,
        "order": order,
        "poster": poster,
        "province": province,
        "work_type": work_type,
        "position": position,
        "salary_kind": salary_kind,

        # choices สำหรับ dropdown
        "provinces": provinces,
        "work_type_choices": work_type_choices,
        "position_choices": position_choices,
    })



@login_required
def approve_post(request, post_id):
    post = get_object_or_404(CoopPost, id=post_id)

    # อนุญาตเฉพาะครู/แอดมิน
    if request.user.role not in ['teacher', 'admin'] and request.user.username != 'admin007':
        return redirect('login')

    post.status = "approved"
    post.save()

    # ---------- ประวัติการอนุมัติ (แท็บ การอนุมัติ) ----------
    Notification.objects.create(
        user=request.user,           # คนอนุมัติ เห็นเป็นประวัติของตัวเอง
        actor=request.user,
        post=post,
        noti_type='approval',
        extra_status='approved',
        message=f"คุณอนุมัติโพสต์ {post.company} ของ {post.owner.first_name}"
    )

    # ---------- แจ้งเตือนเจ้าของโพสต์ว่าผ่าน ----------
    Notification.objects.create(
        user=post.owner,
        actor=request.user,
        post=post,
        noti_type='post',
        message=f"โพสต์ {post.company} ของคุณได้รับการอนุมัติแล้ว"
    )

    # ---------- แจ้งเตือนครู/แอดมินคนอื่น ๆ ว่ามีโพสต์ใหม่ (แท็บ แจ้งเตือน) ----------
    receivers = CustomUser.objects.filter(
        models.Q(role='teacher') | models.Q(role='admin') | models.Q(username='admin007'),
        is_active=True
    ).exclude(id=request.user.id)

    for receiver in receivers:
        Notification.objects.create(
            user=receiver,
            actor=request.user,
            post=post,
            noti_type='post',
            message=f"มีโพสต์ใหม่ที่ผ่านการอนุมัติ: {post.company}"
        )

    return redirect('teacher_home')


@login_required
def reject_post(request, post_id):
    post = get_object_or_404(CoopPost, id=post_id)

    if request.user.role not in ['teacher', 'admin'] and request.user.username != 'admin007':
        return redirect('login')

    post.status = "rejected"
    post.save()

    # ประวัติการอนุมัติ (ไม่ผ่าน)
    Notification.objects.create(
        user=request.user,
        actor=request.user,
        post=post,
        noti_type='approval',
        extra_status='rejected',
        message=f"คุณไม่อนุมัติโพสต์ {post.company} ของ {post.owner.first_name}"
    )

    # แจ้งเจ้าของโพสต์
    Notification.objects.create(
        user=post.owner,
        actor=request.user,
        post=post,
        noti_type='post',
        message=f"โพสต์ {post.company} ของคุณไม่ได้รับการอนุมัติ"
    )

    return redirect('teacher_home')



from django.shortcuts import get_object_or_404

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(CoopPost, id=post_id)
    comments = Comment.objects.filter(post=post).order_by('created_at')

    PostView.objects.create(
        post=post,
        user=request.user
    )

    extra_images = post.extra_images.all()

    if post.position:
        positions = [p.strip() for p in post.position.split(",")]
    else:
        positions = []

    # ✅ เช็คว่า user นี้ bookmark post นี้หรือยัง
    is_bookmarked = False
    if request.user.is_authenticated and request.user.role == 'student':
        is_bookmarked = Bookmark.objects.filter(user=request.user, post=post).exists()

    return render(request, 'post_detail.html', {
        "post": post,
        "comments": comments,
        "extra_images": extra_images,
        "positions": positions,
        "is_bookmarked": is_bookmarked,   # ส่งไป template
    })



@login_required
def add_comment(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(CoopPost, id=post_id)

        comment = Comment.objects.create(
            post=post,
            user=request.user,
            text=request.POST.get("comment")
        )

        # ===== แจ้งเจ้าของโพสต์ =====
        if post.owner != request.user:
            Notification.objects.create(
                user=post.owner,
                actor=request.user,
                post=post,
                comment=comment,
                noti_type='comment',
                message=f"{request.user.first_name} แสดงความคิดเห็นในโพสต์ของคุณ"
            )

        # ===== แจ้งคนที่เคยคอมเมนต์โพสต์นี้มาก่อน =====
        previous_users = CustomUser.objects.filter(
            comment__post=post
        ).exclude(id__in=[request.user.id, post.owner.id]).distinct()

        for u in previous_users:
            Notification.objects.create(
                user=u,
                actor=request.user,
                post=post,
                comment=comment,
                noti_type='comment',
                message=f"{request.user.first_name} แสดงความคิดเห็นในโพสต์ที่คุณเคยร่วมแสดงความคิดเห็น"
            )

    return redirect('post_detail', post_id=post_id)



@login_required
def post_approval_list(request):
    if request.user.role != 'teacher':
        return redirect('login')

    posts = CoopPost.objects.filter(
        owner__major=request.user.major,
        status='pending'
    ).order_by('-created_at')
    
    return render(request, 'post_approval_list.html', {"posts": posts, "user_obj": request.user})

@login_required
def expired_posts(request):
    # อนุญาตเฉพาะครู/แอดมิน
    if request.user.role not in ['teacher', 'admin'] and request.user.username != 'admin007':
        return redirect('login')

    posts = CoopPost.objects.filter(status='expired').order_by('-created_at')
    return render(request, 'expired_posts.html', {"posts": posts, "user_obj": request.user})



@login_required
def post_review_detail(request, post_id):
    if request.user.role != 'teacher':
        return redirect('login')

    post = get_object_or_404(CoopPost, id=post_id)

    # ---- parse work_time: "วันทำงาน 09:00 - 17:00" ----
    work_day = ""
    time_start = ""
    time_end = ""

    if post.work_time:
        # ดึงเวลาแบบ HH:MM - HH:MM ออกมาก่อน
        m = re.search(r'(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})', post.work_time)
        if m:
            time_start, time_end = m.group(1), m.group(2)
            # ส่วนวันทำงาน = ตัดช่วงเวลาออก
            work_day = re.sub(r'\s*\d{2}:\d{2}\s*-\s*\d{2}:\d{2}\s*', '', post.work_time).strip()
        else:
            # ถ้ารูปแบบไม่ตรง ก็โชว์ทั้งสตริงเป็น work_day ไปเลย
            work_day = post.work_time.strip()

    # ---- parse internship_period: "YYYY-MM-DD ถึง YYYY-MM-DD" ----
    start_date = ""
    end_date = ""
    if post.internship_period and " ถึง " in post.internship_period:
        start_date, end_date = [s.strip() for s in post.internship_period.split(" ถึง ", 1)]
    else:
        # ถ้าไม่ตรง format ก็โชว์ทั้งสตริงเป็น start_date
        start_date = post.internship_period or ""

    return render(request, 'post_review_detail.html', {
        "post": post,
        "work_day": work_day,
        "time_start": time_start,
        "time_end": time_end,
        "start_date": start_date,
        "end_date": end_date,
    })

@login_required
def Teacher_approval(request):
    if request.user.username != 'admin007' and request.user.role != 'admin':
        return redirect('login')

    pending_teachers = CustomUser.objects.filter(role='teacher', approved=False)

    approve_id = request.GET.get('approve')
    if approve_id:
        t = CustomUser.objects.get(id=approve_id)
        t.approved = True
        t.save()
        return redirect('teacher_approval')


    return render(request, 'teacher_approval.html', {
        'pending_teachers': pending_teachers
    })

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(CoopPost, id=post_id)

    # อนุญาตเฉพาะอาจารย์หรือแอดมิน
    if request.user.role not in ['teacher', 'admin'] and request.user.username != 'admin007':
        return redirect('login')

    post.status = "deleted"
    post.save()

    messages.success(request, "ลบโพสต์แล้ว (เก็บในถังขยะ)")
    return redirect('admin_dashboard' if request.user.role == 'admin' else 'teacher_home')

@login_required
def toggle_expire_post(request, post_id):
    post = get_object_or_404(CoopPost, id=post_id)

    # อนุญาตเฉพาะอาจารย์หรือแอดมิน
    if request.user.role not in ['teacher', 'admin'] and request.user.username != 'admin007':
        return redirect('login')

    if post.status == "approved":
        post.status = "expired"
        messages.success(request, f"ตั้งค่าโพสต์ของ {post.company} เป็นหมดอายุ/ปิดรับสมัครเรียบร้อยแล้ว")
    elif post.status == "expired":
        from django.utils import timezone
        post.status = "approved"
        post.created_at = timezone.now()
        messages.success(request, f"เปิดรับสมัครโพสต์ของ {post.company} อีกครั้งเรียบร้อยแล้ว (ต่ออายุโพสต์ต่ออีก 3 เดือน)")

    post.save()
    next_url = request.META.get('HTTP_REFERER') or reverse('teacher_home')
    return redirect(next_url)

@login_required
def trash_bin(request):
    if request.user.role not in ['teacher', 'admin'] and request.user.username != 'admin007':
        return redirect('login')

    posts = CoopPost.objects.filter(status='deleted')

    return render(request, 'trash_bin.html', {
        "posts": posts,
        "user_obj": request.user
    })


@login_required
def restore_post(request, post_id):
    post = get_object_or_404(CoopPost, id=post_id)
    post.status = "approved"
    post.save()
    messages.success(request, "กู้คืนโพสต์สำเร็จ")
    return redirect('trash_bin')


@login_required
def trash_bin(request):
    if request.user.role not in ['teacher', 'admin'] and request.user.username != 'admin007':
        return redirect('login')

    deleted_posts = CoopPost.objects.filter(status="deleted").order_by('-created_at')

    return render(request, "trash_bin.html", {
        "posts": deleted_posts,
        "user_obj": request.user,
    })


@login_required
def restore_post(request, post_id):
    post = get_object_or_404(CoopPost, id=post_id)
    post.status = "approved"   # ⭐ กู้คืน
    post.save()

    messages.success(request, "กู้คืนโพสต์สำเร็จ")
    return redirect('trash_bin')

# ---------- หน้าหลังจากโพสต์สำเร็จ ----------
@login_required
def post_success(request):
    return render(request, 'post_success.html')

@login_required
def restore_post(request, post_id):
    post = get_object_or_404(CoopPost, id=post_id)

    # คืนสถานะให้เป็น approved (กลับไปโชว์ทุก role)
    post.status = "approved"
    post.save()

    messages.success(request, "กู้คืนโพสต์สำเร็จ")
    return redirect('trash_bin')


from django.http import HttpResponseRedirect
from django.urls import reverse

@login_required
def toggle_bookmark(request, post_id):
    # อนุญาตเฉพาะ student
    if request.user.role != 'student':
        return redirect('login')

    post = get_object_or_404(CoopPost, id=post_id)

    if request.method == "POST":
        bookmark, created = Bookmark.objects.get_or_create(
            user=request.user,
            post=post
        )
        if not created:
            # ถ้ามีอยู่แล้ว = กดซ้ำเพื่อลบออก
            bookmark.delete()

    # กลับไปหน้าเดิม (ถ้ามี next) ไม่ก็มาที่ student_home
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse('student_home')
    return HttpResponseRedirect(next_url)

@login_required
def bookmark_list(request):
    if request.user.role != 'student':
        return redirect('login')

    bookmarks = Bookmark.objects.filter(user=request.user).select_related('post')

    return render(request, 'bookmark_list.html', {
        "user_obj": request.user,
        "bookmarks": bookmarks,
    })


@login_required
def activity_view(request):
    # ใช้ได้เฉพาะครู+แอดมิน
    if request.user.role not in ['teacher', 'admin'] and request.user.username != 'admin007':
        return redirect('login')

    tab = request.GET.get('tab', 'alert')   # alert | comment | review | approval

    qs = Notification.objects.filter(user=request.user)

    if tab == 'comment':
        qs = qs.filter(noti_type='comment')
    elif tab == 'review':
        qs = qs.filter(noti_type='review')
    elif tab == 'approval':
        qs = qs.filter(noti_type='approval')
    else:   # 'alert'
        qs = qs.filter(noti_type='post')

    notifications = qs.select_related('actor', 'post', 'post__owner')

    return render(request, 'activity.html', {
        'user_obj': request.user,
        'notifications': notifications,
        'current_tab': tab,
    })


@login_required
def activity_student_view(request):
    # ใช้ได้เฉพาะนักศึกษา
    if request.user.role != 'student':
        return redirect('login')

    tab = request.GET.get('tab', 'alert')   # alert | status | comment

    # ---------- แท็บ แจ้งเตือนทั่วไป ----------
    if tab == 'comment':
        notifications = Notification.objects.filter(
            user=request.user,
            noti_type='comment',
            post__isnull=False
        ).select_related('actor', 'post', 'post__owner')

        return render(request, 'activitystuden.html', {
            'user_obj': request.user,
            'current_tab': tab,
            'notifications': notifications,
            'posts': [],
        })

    # ---------- แท็บ สถานะโพสต์ ----------
    if tab == 'status':
        posts = list(
            CoopPost.objects.filter(
                owner=request.user
            ).exclude(status='deleted').order_by('-created_at')
        )

        # หาอาจารย์คนล่าสุดที่อนุมัติ / ไม่อนุมัติจาก Notification
        for p in posts:
            latest_noti = Notification.objects.filter(
                user=request.user,
                post=p,
                noti_type='post',
                actor__role__in=['teacher', 'admin']
            ).order_by('-created_at').first()
            p.last_approver = latest_noti.actor if latest_noti else None

        return render(request, 'activitystuden.html', {
            'user_obj': request.user,
            'current_tab': tab,
            'notifications': [],
            'posts': posts,
        })

    # ---------- แท็บ แจ้งเตือน (ค่าเริ่มต้น) ----------
    notifications = Notification.objects.filter(
        user=request.user,
        noti_type='post',
        post__isnull=False
    ).select_related('actor', 'post', 'post__owner')

    return render(request, 'activitystuden.html', {
        'user_obj': request.user,
        'current_tab': 'alert',
        'notifications': notifications,
        'posts': [],
    })


# ---------- หน้าบันทึกกิจกรรม (ประวัติโพสต์ของตัวเอง) ----------
@login_required
def activity_history(request):
    # ดึงเฉพาะโพสต์ของ user คนนี้ (ไม่เอา status = deleted)
    posts = CoopPost.objects.filter(
        owner=request.user
    ).exclude(status="deleted").order_by('-created_at')

    return render(request, 'activity_history.html', {
        'user_obj': request.user,
        'posts': posts,
    })


# ---------- แก้ไขโพสต์ ----------
@login_required
def edit_post(request, post_id):
    post = get_object_or_404(CoopPost, id=post_id)

    # อนุญาตให้แก้เฉพาะเจ้าของโพสต์ หรือ แอดมิน/อาจารย์
    if (post.owner != request.user and
        request.user.role not in ['teacher', 'admin'] and
        request.user.username != 'admin007'):
        return redirect('login')

    # แยกค่าจาก field เดิม เพื่อนำไปเติมในฟอร์ม
    # work_time เช่น "จันทร์ - ศุกร์ 09:00 - 17:00"
    work_day = ""
    time_start = ""
    time_end = ""
    if post.work_time:
        try:
            work_day, times = post.work_time.split(' ', 1)
            time_start, time_end = times.split(' - ')
        except ValueError:
            pass

    # internship_period เช่น "2025-01-01 ถึง 2025-05-31"
    start_date = ""
    end_date = ""
    if post.internship_period:
        try:
            start_date, end_date = post.internship_period.split(' ถึง ')
        except ValueError:
            pass

    # ตำแหน่งหลายตัว
    positions = [p.strip() for p in post.position.split(',')] if post.position else [""]

    if request.method == "POST":
        # ------- ดึงค่าจากฟอร์มเหมือน create_post -------
        work_time = f"{request.POST.get('work_day')} {request.POST.get('time_start')} - {request.POST.get('time_end')}"
        internship_period = f"{request.POST.get('start_date')} ถึง {request.POST.get('end_date')}"

        salary_type = request.POST.get('salary_type')
        salary_amount = request.POST.get('salary_amount')

        if salary_type == "มี" and salary_amount:
            salary = f"{salary_amount} บาท"
        else:
            salary = salary_type

        positions_list = request.POST.getlist('positions[]')
        positions_list = [p.strip() for p in positions_list if p.strip()]
        positions_str = ", ".join(positions_list)

        portfolio = request.POST.get("portfolio") or ""
        extra_link = request.POST.get("extra_link") or ""
        checkin_location = request.POST.get("checkin_location") or ""

        # อัปเดต field ต่าง ๆ
        post.company = request.POST.get('company')
        post.province = request.POST.get('province')
        post.salary = salary
        post.position = positions_str
        post.work_time = work_time
        post.internship_period = internship_period
        post.location = request.POST.get('location')
        post.checkin_location = checkin_location
        post.skills = request.POST.get('skills')
        post.grade = request.POST.get('grade')
        post.contact = request.POST.get('contact')
        post.type_of_work = request.POST.get('type_of_work')
        post.description = request.POST.get('description')
        post.portfolio = portfolio
        post.extra_link = extra_link

        # ถ้ามีอัปโหลดรูปใหม่ ให้แทนที่รูปเดิม
        if request.FILES.get('image'):
            post.image = request.FILES['image']

        # ถ้ามีไฟล์เพิ่มเติม / วิดีโอใหม่ ก็อัปเดต
        if request.FILES.get('extra_file'):
            post.extra_file = request.FILES['extra_file']

        if request.FILES.get('extra_video'):
            post.video = request.FILES['extra_video']

        post.save()

        # ถ้ามีอัปโหลดรูปประกอบใหม่ ๆ ให้เพิ่มเข้าไป (ไม่ลบของเก่า)
        extra_images = request.FILES.getlist('extra_images')
        for img in extra_images:
            CoopPostImage.objects.create(post=post, image=img)

        messages.success(request, "แก้ไขโพสต์เรียบร้อยแล้ว")
        return redirect('post_detail', post_id=post.id)

    # ----- ถ้าเป็น GET ให้เปิดฟอร์มพร้อมข้อมูลเดิม -----
    return render(request, 'post_edit.html', {
        "user": request.user,
        "post": post,
        "provinces": PROVINCES,
        "positions": positions,
        "work_day": work_day,
        "time_start": time_start,
        "time_end": time_end,
        "start_date": start_date,
        "end_date": end_date,
    })

# myapp/views.py (ต่อจาก import ด้านบนมีแล้ว: CoopPost, Comment, Bookmark, Notification ...)

from django.db.models import Count

from django.db.models import Count

@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        return redirect('login')

    # 1) จำนวนเข้าชมโพสต์ของตัวเอง
    my_views = PostView.objects.filter(
        post__owner=request.user
    ).count()

    # 2) จำนวนแสดงความคิดเห็นในโพสต์ตัวเอง
    my_comments = Comment.objects.filter(
        post__owner=request.user
    ).count()

    # 3) จำนวนจัดเก็บเข้าชั้นในโพสต์ตัวเอง (คนอื่น bookmark โพสต์ของเรา)
    my_bookmarks = Bookmark.objects.filter(
        post__owner=request.user
    ).count()

    # 4) จำนวนเข้าชมทั้งหมด
    total_views = PostView.objects.all().count()

    # 5) จำนวนแสดงความคิดเห็นทั้งหมด
    total_comments = Comment.objects.all().count()

    # 6) จำนวนจัดเก็บเข้าชั้นทั้งหมด
    total_bookmarks = Bookmark.objects.all().count()

    context = {
        "user_obj": request.user,
        "my_views": my_views,
        "my_comments": my_comments,
        "my_bookmarks": my_bookmarks,
        "total_views": total_views,
        "total_comments": total_comments,
        "total_bookmarks": total_bookmarks,
    }
    return render(request, "student_dashboard.html", context)


# สีสำหรับ pie chart 6 สีวนซ้ำ
CHART_COLORS = ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40"]


def make_pie_data(qs):
    """
    qs ต้องเป็น .values('post__id','post__company').annotate(c=Count('id'))
    คืนค่า (list ของข้อมูลแต่ละโพสต์, string สำหรับ conic-gradient)
    """
    data = []
    for idx, row in enumerate(qs):
        data.append({
            "company": row["post__company"],
            "count": row["c"],
            "color": CHART_COLORS[idx % len(CHART_COLORS)],
        })

    total = sum(d["count"] for d in data) or 1
    parts = []
    current = 0.0

    for d in data:
        portion = d["count"] / total * 100.0
        start = current
        end = current + portion
        parts.append(f"{d['color']} {start:.2f}% {end:.2f}%")
        current = end

    gradient = "conic-gradient(" + ", ".join(parts) + ")" if data else "#ffffff"
    return data, gradient


@login_required
def management_dashboard(request):
    """
    แดชบอร์ดรวมสำหรับ role อาจารย์ + แอดมิน (รวม admin007 ด้วย)
    """
    if request.user.role not in ["teacher", "admin"] and request.user.username != "admin007":
        return redirect("login")

    # ----- ตัวเลขด้านบน -----
    total_students = CustomUser.objects.filter(role="student").count()
    total_posts = CoopPost.objects.exclude(status="deleted").count()
    total_bookmarks = Bookmark.objects.all().count()

    # ----- ตัวเลขด้านล่าง (ของคุณ/ทั้งหมด) -----
    my_views = PostView.objects.filter(post__owner=request.user).count()
    total_views = PostView.objects.all().count()
    my_bookmarks = Bookmark.objects.filter(post__owner=request.user).count()

    # ----- ข้อมูลต่อโพสต์เอาไปทำเป็น pie chart (เอาแค่ top 6) -----
    my_views_qs = (
        PostView.objects.filter(post__owner=request.user)
        .values("post__id", "post__company")
        .annotate(c=Count("id"))
        .order_by("-c")[:6]
    )

    all_views_qs = (
        PostView.objects.all()
        .values("post__id", "post__company")
        .annotate(c=Count("id"))
        .order_by("-c")[:6]
    )

    my_bookmarks_qs = (
        Bookmark.objects.filter(post__owner=request.user)
        .values("post__id", "post__company")
        .annotate(c=Count("id"))
        .order_by("-c")[:6]
    )

    my_views_data, my_views_gradient = make_pie_data(my_views_qs)
    all_views_data, all_views_gradient = make_pie_data(all_views_qs)
    my_bookmarks_data, my_bookmarks_gradient = make_pie_data(my_bookmarks_qs)

    context = {
        "user_obj": request.user,

        # ตัวเลข row บน
        "total_students": total_students,
        "total_posts": total_posts,
        "total_bookmarks": total_bookmarks,

        # ตัวเลข row ล่าง
        "my_views": my_views,
        "total_views": total_views,
        "my_bookmarks": my_bookmarks,

        # data สำหรับ pie + legend
        "my_views_data": my_views_data,
        "all_views_data": all_views_data,
        "my_bookmarks_data": my_bookmarks_data,

        "my_views_gradient": my_views_gradient,
        "all_views_gradient": all_views_gradient,
        "my_bookmarks_gradient": my_bookmarks_gradient,
    }

    return render(request, "management_dashboard.html", context)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Exists, OuterRef

from .models import CustomUser

from django.contrib.auth.decorators import login_required
from django.db.models import Exists, OuterRef

from .models import CustomUser, CoopPost


@login_required
def member_list(request):
    # ดึงเฉพาะ role นักศึกษา
    students = CustomUser.objects.filter(role='student')

    # ถ้าเป็นอาจารย์ให้ดูเฉพาะนักศึกษาคณะ/สาขาเดียวกัน
    if request.user.role == 'teacher':
        students = students.filter(
            faculty=request.user.faculty,
            major=request.user.major
        )

    # มีโพสต์ของตัวเองที่ status = "approved" อย่างน้อย 1 อันไหม
    approved_posts = CoopPost.objects.filter(
        owner=OuterRef('pk'),
        status='approved'
    )

    # เพิ่มฟิลด์เสมือน has_approved_post (True / False) ให้แต่ละ student
    students = students.annotate(
        has_approved_post=Exists(approved_posts)
    ).order_by('first_name', 'last_name')

    return render(request, 'member_list.html', {'students': students})

# myapp/views.py
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .models import CoopPost

@login_required
@require_POST
def empty_trash(request):
    # อนุญาตเฉพาะอาจารย์/แอดมิน/แอดมินพิเศษ
    if request.user.role not in ['teacher', 'admin'] and request.user.username != 'admin007':
        return redirect('login')

    # ลบถาวรเฉพาะที่อยู่ในถังขยะ
    CoopPost.objects.filter(status='deleted').delete()

    messages.success(request, "ลบถาวรเรียบร้อยแล้ว")
    return redirect('trash_bin')


# myapp/views.py
from django.db.models import Q

# (แนะนำ) ทำเป็นลิสต์ใช้ใน dropdown ตำแหน่ง
POSITION_CHOICES = [
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "Mobile Developer",
    "DevOps Engineer",
    "Data Analyst",
    "Data Engineer",
    "Data Scientist",
    "Software Tester",
    "QA Engineer",
    "UI/UX Designer",
]

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from .models import CustomUser

def _is_admin(user):
    # ปรับเงื่อนไขให้ตรงกับระบบ role ของคุณ
    return getattr(user, "role", "") == "admin" or user.username == "admin007"

@login_required
def manage_accounts(request):
    if not _is_admin(request.user):
        return HttpResponseForbidden("คุณไม่มีสิทธิ์เข้าหน้านี้")

    q = request.GET.get("q", "").strip()
    users = CustomUser.objects.all().order_by("-id")

    if q:
        users = users.filter(
            # ปรับ field ตามที่มีจริงใน CustomUser ของคุณ
            # ตัวอย่าง: first_name, last_name, username, email, student_id
            # ใช้ icontains เพื่อค้นหาแบบไม่สนตัวพิมพ์เล็กใหญ่
        )

        # ถ้าคุณมี student_id แน่ๆ ใช้แบบนี้ได้:
        # from django.db.models import Q
        # users = users.filter(
        #     Q(first_name__icontains=q) |
        #     Q(last_name__icontains=q) |
        #     Q(username__icontains=q) |
        #     Q(email__icontains=q) |
        #     Q(student_id__icontains=q)
        # )

        # แต่เพื่อไม่ให้ error ถ้า field บางตัวไม่มี ให้ใช้ขั้นต่ำสุดก่อน:
        from django.db.models import Q
        users = users.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(username__icontains=q) |
            Q(email__icontains=q)
        )

    return render(request, "manage_accounts.html", {
        "users": users,
        "q": q
    })

@login_required
def delete_user(request, user_id):
    if not _is_admin(request.user):
        return HttpResponseForbidden("คุณไม่มีสิทธิ์ลบผู้ใช้")

    if request.method != "POST":
        return HttpResponseForbidden("Method not allowed")

    target = get_object_or_404(CustomUser, id=user_id)

    # กันลบตัวเอง
    if target.id == request.user.id:
        messages.error(request, "ไม่สามารถลบบัญชีของตัวเองได้")
        return redirect("manage_accounts")

    # กันลบ superuser (ถ้าคุณใช้ระบบ Django admin ด้วย)
    if hasattr(target, "is_superuser") and target.is_superuser:
        messages.error(request, "ไม่สามารถลบ superuser ได้")
        return redirect("manage_accounts")

    target.delete()
    messages.success(request, "ลบผู้ใช้งานสำเร็จ")
    return redirect("manage_accounts")