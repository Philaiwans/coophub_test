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

def home_redirect(request):
    return redirect('login')


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

        # =============== ส่งอีเมลยืนยัน ===============
        current_site = get_current_site(request)
        mail_subject = 'ยืนยันอีเมลเพื่อเปิดใช้งานบัญชี CoopHub'

        message = render_to_string('email_verification.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })

        email_message = EmailMessage(
            mail_subject,
            message,
            to=[email]
        )
        email_message.content_subtype = "html"  # ส่ง HTML email
        email_message.send()
        # ==============================================

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
from .models import CoopPost, Comment, CustomUser, CoopPostImage


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

    return render(request, 'student_home.html', {
        "user_obj": request.user,
        "posts": posts,
        "search": search,
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

        # 1) รวมเวลาทำงาน เช่น "จันทร์-ศุกร์ 09:00 - 17:00"
        work_time = f"{request.POST.get('work_day')} {request.POST.get('time_start')} - {request.POST.get('time_end')}"

        # 2) รวมช่วงฝึกงาน
        internship_period = f"{request.POST.get('start_date')} ถึง {request.POST.get('end_date')}"

        # 3) เบี้ยเลี้ยง
        salary_type = request.POST.get('salary_type')       # ไม่มี / มี / ตามตกลง
        salary_amount = request.POST.get('salary_amount')   # จำนวนเงิน (ถ้าเลือก "มี")

        if salary_type == "มี" and salary_amount:
            salary = f"{salary_amount} บาท"
        else:
            salary = salary_type

        # 4) ดึง “หลายตำแหน่ง” จากฟอร์ม
        positions_list = request.POST.getlist('positions[]')    # ['Frontend', 'Backend', ...]
        positions_list = [p.strip() for p in positions_list if p.strip()]
        positions_str = ", ".join(positions_list)               # 'Frontend, Backend'

        # 5) ข้อมูลอื่น ๆ
        portfolio = request.POST.get("portfolio") or ""
        extra_link = request.POST.get("extra_link") or ""   # (ถ้าจะใช้ในอนาคต)
        checkin_location = request.POST.get("checkin_location") or ""

        # 6) สร้าง object CoopPost (แต่ยังไม่ save รูปประกอบหลายรูป)
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

        # 7) ไฟล์เดี่ยว (ปก, ไฟล์แนบ, วิดีโอ)
        if request.FILES.get('image'):
            post.image = request.FILES['image']

        if request.FILES.get('extra_file'):
            post.extra_file = request.FILES['extra_file']

        if request.FILES.get('extra_video'):
            post.video = request.FILES['extra_video']

        # 8) สถานะโพสต์
        if request.user.role == 'teacher' or request.user.username == 'admin007':
            post.status = "approved"
        else:
            post.status = "pending"

        # ต้อง save ก่อน ถึงจะเอาไปผูกกับ CoopPostImage ได้
        post.save()

        # 9) รูปประกอบหลายรูป
        extra_images = request.FILES.getlist('extra_images')
        for img in extra_images:
            CoopPostImage.objects.create(post=post, image=img)

        return redirect("post_success")

    # 10) GET → ส่งรายชื่อจังหวัดเข้าไป
    return render(request, 'post_create.html', {
        "provinces": PROVINCES
    })




@login_required
def teacher_home(request):
    if request.user.role != 'teacher':
        return redirect('login')

    search = request.GET.get("search", "").strip()

    # อาจารย์เห็นทุกโพสต์ที่ status = approved เหมือนนักศึกษา
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

    return render(request, 'teacher_home.html', {
        "user_obj": request.user,
        "posts": posts,
        "search": search,
    })



@login_required
def approve_post(request, post_id):
    post = CoopPost.objects.get(id=post_id)
    post.status = "approved"
    post.save()
    return redirect('teacher_home')


@login_required
def reject_post(request, post_id):
    post = CoopPost.objects.get(id=post_id)
    post.status = "rejected"
    post.save()
    return redirect('teacher_home')


from django.shortcuts import get_object_or_404

@login_required
def post_detail(request, post_id):
    post = get_object_or_404(CoopPost, id=post_id)
    comments = Comment.objects.filter(post=post).order_by('created_at')

    # รูปประกอบเพิ่มเติม
    extra_images = post.extra_images.all()  # ถ้าใช้ CoopPostImage แล้ว

    # ✅ แยกตำแหน่งออกเป็น list ตั้งแต่ใน view
    if post.position:
        positions = [p.strip() for p in post.position.split(",")]
    else:
        positions = []

    return render(request, 'post_detail.html', {
        "post": post,
        "comments": comments,
        "extra_images": extra_images,
        "positions": positions,      # ส่ง list ไป template
    })



@login_required
def add_comment(request, post_id):
    if request.method == "POST":
        Comment.objects.create(
            post_id=post_id,
            user=request.user,
            text=request.POST.get("comment")
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

    return render(request, 'post_approval_list.html', {"posts": posts})


@login_required
def post_review_detail(request, post_id):
    if request.user.role != 'teacher':
        return redirect('login')

    post = get_object_or_404(CoopPost, id=post_id)

    return render(request, 'post_review_detail.html', {"post": post})

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
