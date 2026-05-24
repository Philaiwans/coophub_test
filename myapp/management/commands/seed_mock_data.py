from django.core.management.base import BaseCommand
from django.utils import timezone

from myapp.models import CustomUser, CoopPost


class Command(BaseCommand):
    help = "Seed mock data: 10 students (5 with posts, 5 without) and 3 teachers"

    def handle(self, *args, **options):
        # ====== ตั้งค่าพื้นฐาน ======
        DEFAULT_PASSWORD = "Test12345!"
        faculty = "คณะวิทยาศาสตร์"
        major = "วิทยาการข้อมูลและนวัตกรรมซอฟต์แวร์"

        # กันรันซ้ำ: ถ้ามี username เหล่านี้แล้วจะไม่สร้างซ้ำ
        usernames_to_create = (
            [f"std{i:02d}" for i in range(1, 11)] +
            [f"tch{i:02d}" for i in range(1, 4)]
        )
        existing = set(CustomUser.objects.filter(username__in=usernames_to_create).values_list("username", flat=True))

        created_users = []

        # ====== 1) สร้างอาจารย์ 3 คน ======
        teacher_specs = [
            dict(username="tch01", first_name="อาจารย์", last_name="ศิริพร", email="tch01@ubu.ac.th"),
            dict(username="tch02", first_name="อาจารย์", last_name="ธนากร", email="tch02@ubu.ac.th"),
            dict(username="tch03", first_name="อาจารย์", last_name="ปวีณ์",  email="tch03@ubu.ac.th"),
        ]

        for t in teacher_specs:
            if t["username"] in existing:
                continue
            u = CustomUser.objects.create_user(
                username=t["username"],
                email=t["email"],
                password=DEFAULT_PASSWORD,
                role="teacher",
                first_name=t["first_name"],
                last_name=t["last_name"],
                faculty=faculty,
                major=major,
                is_active=True,      # ให้ล็อกอินได้เลย
                approved=True,       # อาจารย์ผ่านอนุมัติแล้ว
            )
            created_users.append(u)

        # ====== 2) สร้างนักศึกษา 10 คน ======
        # 5 คนแรกมีโพสต์, อีก 5 คนไม่มีโพสต์
        student_specs = []
        for i in range(1, 11):
            student_specs.append(dict(
                username=f"std{i:02d}",
                first_name="นักศึกษา",
                last_name=f"ทดสอบ{i:02d}",
                email=f"std{i:02d}@ubu.ac.th",
                student_id=f"6611454{i:03d}",  # ปรับได้ตามต้องการ
            ))

        students = []
        for s in student_specs:
            if s["username"] in existing:
                # ถ้ามีอยู่แล้ว ดึงมาใช้งานต่อ (เผื่ออยากสร้างโพสต์เพิ่ม)
                u = CustomUser.objects.filter(username=s["username"]).first()
                if u:
                    students.append(u)
                continue

            u = CustomUser.objects.create_user(
                username=s["username"],
                email=s["email"],
                password=DEFAULT_PASSWORD,
                role="student",
                first_name=s["first_name"],
                last_name=s["last_name"],
                student_id=s["student_id"],
                faculty=faculty,
                major=major,
                is_active=True,
                approved=True,   # นักศึกษาถือว่า approved ได้เลยตามระบบคุณ
            )
            created_users.append(u)
            students.append(u)

        # ถ้ามีบางคนถูกสร้างไว้ก่อนแล้ว students อาจ < 10 (เพราะดึงจาก DB)
        # จัดเรียงให้แน่นอน
        students = list(CustomUser.objects.filter(username__startswith="std").order_by("username")[:10])

        # ====== 3) สร้างโพสต์ให้ 5 คนแรก ======
        # (status จะเป็น pending ตาม logic ระบบคุณเวลานักศึกษาสร้างโพสต์ผ่าน view
        # แต่ seed ใน DB เรากำหนดได้เลยว่าต้องการให้เห็นในฟีดหรือยัง)
        post_templates = [
            dict(
                company="SCG Digital",
                province="กรุงเทพมหานคร",
                salary="300 บาท",
                position="Data Analyst, Data Engineer",
                work_time="จันทร์-ศุกร์ 09:00 - 17:00",
                internship_period="2026-06-01 ถึง 2026-09-30",
                location="บางซื่อ กรุงเทพฯ",
                checkin_location="https://maps.google.com/?q=Bang+Sue",
                skills="Python, SQL, Power BI",
                grade="2.50",
                contact="hr@scg.com / Line: @scgcareers",
                type_of_work="Hybrid",
                description="งานวิเคราะห์ข้อมูลและทำแดชบอร์ดให้ทีมธุรกิจ",
                status="approved",
            ),
            dict(
                company="True Digital Group",
                province="กรุงเทพมหานคร",
                salary="ตามตกลง",
                position="Backend Developer",
                work_time="จันทร์-ศุกร์ 10:00 - 19:00",
                internship_period="2026-06-01 ถึง 2026-10-31",
                location="ห้วยขวาง กรุงเทพฯ",
                checkin_location="",
                skills="Django, REST API, PostgreSQL",
                grade="2.75",
                contact="recruit@trueid.net",
                type_of_work="On-site",
                description="พัฒนา API และเชื่อมต่อฐานข้อมูลให้ระบบภายใน",
                status="approved",
            ),
            dict(
                company="PTT Digital",
                province="กรุงเทพมหานคร",
                salary="ไม่มี",
                position="UI/UX Designer",
                work_time="จันทร์-ศุกร์ 09:30 - 18:30",
                internship_period="2026-05-15 ถึง 2026-08-15",
                location="จตุจักร กรุงเทพฯ",
                checkin_location="",
                skills="Figma, User Research, Prototype",
                grade="3.00",
                contact="ux@pttdigital.co.th",
                type_of_work="Hybrid",
                description="ออกแบบหน้าจอและทำ usability test เบื้องต้น",
                status="approved",
            ),
            dict(
                company="KBTG",
                province="กรุงเทพมหานคร",
                salary="400 บาท",
                position="Frontend Developer",
                work_time="จันทร์-ศุกร์ 09:00 - 18:00",
                internship_period="2026-06-10 ถึง 2026-09-10",
                location="สุขุมวิท กรุงเทพฯ",
                checkin_location="",
                skills="HTML, Tailwind CSS, JavaScript",
                grade="2.90",
                contact="talent@kbtg.tech",
                type_of_work="On-site",
                description="พัฒนา UI และเชื่อมต่อหน้าเว็บกับ API",
                status="approved",
            ),
            dict(
                company="AIS Next",
                province="กรุงเทพมหานคร",
                salary="ตามตกลง",
                position="QA Engineer, Software Tester",
                work_time="จันทร์-ศุกร์ 09:00 - 17:30",
                internship_period="2026-06-01 ถึง 2026-09-01",
                location="พหลโยธิน กรุงเทพฯ",
                checkin_location="",
                skills="Test case, Postman, Bug report",
                grade="2.60",
                contact="aisnext@ais.co.th",
                type_of_work="Hybrid",
                description="ช่วยทีม QA เขียน test case และทดสอบระบบเว็บ",
                status="approved",
            ),
        ]

        # กันโพสต์ซ้ำ: ถ้า user มีโพสต์อยู่แล้ว จะไม่เพิ่มใหม่
        created_posts = 0
        for idx, owner in enumerate(students[:5]):
            if CoopPost.objects.filter(owner=owner).exists():
                continue

            data = post_templates[idx % len(post_templates)]
            CoopPost.objects.create(
                owner=owner,
                company=data["company"],
                province=data["province"],
                salary=data["salary"],
                position=data["position"],
                work_time=data["work_time"],
                internship_period=data["internship_period"],
                location=data["location"],
                checkin_location=data["checkin_location"],
                skills=data["skills"],
                grade=data["grade"],
                contact=data["contact"],
                type_of_work=data["type_of_work"],
                description=data["description"],
                status=data["status"],
                # image/extra_file/video เว้นว่างได้
            )
            created_posts += 1

        # ====== สรุปผล ======
        total_students = CustomUser.objects.filter(role="student").count()
        total_teachers = CustomUser.objects.filter(role="teacher").count()
        total_posts = CoopPost.objects.count()

        self.stdout.write(self.style.SUCCESS("Seed completed!"))
        self.stdout.write(f"- Created users this run: {len(created_users)}")
        self.stdout.write(f"- Created posts this run: {created_posts}")
        self.stdout.write(f"- Total students in DB: {total_students}")
        self.stdout.write(f"- Total teachers in DB: {total_teachers}")
        self.stdout.write(f"- Total posts in DB: {total_posts}")
        self.stdout.write(self.style.WARNING(f"All created users use password: {DEFAULT_PASSWORD}"))