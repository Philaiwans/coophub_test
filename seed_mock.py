import os
import django
import random
from datetime import date, timedelta

# ✅ สำคัญ: ปรับให้ตรงชื่อ settings ของโปรเจกต์คุณ
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
django.setup()

from myapp.models import CustomUser, CoopPost  # noqa

# =========================
# CONFIG
# =========================
N_STUDENTS = 10
N_TEACHERS = 10
N_POSTS = 300
DEFAULT_PASSWORD = "12345678"
random.seed(42)

# =========================
# majorData (ตามที่คุณให้มา)
# =========================
MAJOR_DATA = {
    "คณะวิทยาศาสตร์": [
        "ฟิสิกส์ชีวการแพทย์", "ชีววิทยา", "จุลชีววิทยา", "เคมี",
        "วิทยาการข้อมูลและนวัตกรรมซอฟต์แวร์",
        "เทคโนโลยีสารสนเทศและการสื่อสาร",
        "คณิตศาสตร์", "อาชีวอนามัยและความปลอดภัย",
        "วิทยาศาสตร์สิ่งแวดล้อม",
        "เทคโนโลยียางและพอลิเมอร์",
        "นวัตกรรมเทคโนโลยีวัสดุ"
    ],
    "คณะเกษตรศาสตร์": ["เกษตรศาสตร์", "เทคโนโลยีการอาหาร", "เกษตรวิศว์อัจฉริยะ"],
    "คณะวิศวกรรมศาสตร์": [
        "วิศวกรรมเครื่องกล","วิศวกรรมอุตสาหการ","วิศวกรรมเคมี",
        "วิศวกรรมโยธา","วิศวกรรมไฟฟ้า","วิศวกรรมสิ่งแวดล้อม",
        "วิศวกรรมเมคคาทรอนิกส์และระบบอัตโนมัติ",
        "วิศวกรรมปัญญาประดิษฐ์และการสั่งการ"
    ],
    "คณะศิลปศาสตร์": [
        "ภาษาอังกฤษและการสื่อสาร","การจัดการการท่องเที่ยวและการบริการ",
        "นวัตกรรมการพัฒนาสังคม","ภาษาจีนและการสื่อสาร",
        "ภาษาไทยและการสื่อสาร","ภาษาญี่ปุ่นและการสื่อสาร",
        "นิเทศศาสตร์","ภาษาอังกฤษเพื่อธุรกิจในยุคดิจิทัล","ประวัติศาสตร์"
    ],
    "คณะบริหารศาสตร์": [
        "การจัดการธุรกิจ","การตลาด","การเงินและการลงทุน",
        "นวัตกรรมการจัดการโรงแรมและการบริการ",
        "การจัดการธุรกิจระหว่างประเทศ","บัญชี",
        "การจัดการโลจิสติกส์และโซ่อุปทาน"
    ],
    "คณะนิติศาสตร์": ["นิติศาสตร์"],
    "คณะรัฐศาสตร์": ["การปกครอง","รัฐประศาสนศาสตร์"],
    "คณะศึกษาศาสตร์": ["ศึกษาศาสตร์"],
    "คณะเภสัชศาสตร์": ["เภสัชศาสตร์"],
    "คณะพยาบาลศาสตร์": ["พยาบาลศาสตร์"],
    "วิทยาลัยแพทยศาสตร์และการสาธารณสุข": [
        "แพทยศาสตร์","อนามัยสิ่งแวดล้อม","สาธารณสุขศาสตร์"
    ]
}

FACULTIES = list(MAJOR_DATA.keys())

# =========================
# Random pools
# =========================
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
    "อุตรดิตถ์","อุทัยธานี","อุบลราชธานี","ต่างประเทศ",
]
WORK_TYPES = ["On-site", "Online", "Hybrid"]
WORK_DAYS = ["จันทร์-ศุกร์", "จันทร์-เสาร์", "จันทร์-พฤหัส", "อังคาร-เสาร์"]
TIME_SLOTS = [("08:30","16:30"), ("09:00","17:00"), ("09:30","17:30"), ("10:00","18:00")]
SALARY_MODES = ["none", "negotiable", "paid"]

POSITIONS = [
    "Frontend Developer","Backend Developer","Full Stack Developer","Mobile Developer",
    "DevOps Engineer","Data Analyst","Data Engineer","Data Scientist",
    "Software Tester","QA Engineer","UI/UX Designer",
    "Business Analyst","Digital Marketing","Graphic Designer",
    "IoT Engineer","Network Engineer","Project Coordinator",
]
SKILLS_POOL = [
    "HTML","CSS","JavaScript","TypeScript","React","Vue","Django","FastAPI",
    "Python","SQL","MySQL","PostgreSQL","Power BI","Excel","Figma",
    "Docker","Linux","AWS","Git","Jira","Postman","Testing","REST API",
]
CONTACTS = [
    "Line: hr_coophub",
    "โทร 081-234-5678",
    "Email: hr@company.com",
    "Line: coop_hr_team",
    "โทร 089-999-1234",
]
LOCATIONS = [
    "ใกล้ BTS/MRT เดินทางสะดวก",
    "อาคารสำนักงานใจกลางเมือง",
    "นิคมอุตสาหกรรม",
    "โซนมหาวิทยาลัย/หอพักใกล้เคียง",
    "ทำงานแบบ Remote ได้บางวัน",
]
DESCRIPTIONS = [
    "มีพี่เลี้ยงดูแล ทำงานร่วมทีมจริง มี code review",
    "ได้ฝึกทำเอกสาร requirement และสื่อสารกับทีม",
    "ทำโปรเจกต์จริง ส่งมอบงานเป็นรอบ ๆ เรียนรู้ workflow",
    "มีโอกาสได้ทำ Dashboard/Report ให้ผู้บริหาร",
    "เน้นฝึกพื้นฐาน + ลงมือทำจริง เหมาะกับมือใหม่",
    "มี standup/weekly meeting และใช้ Jira/Trello",
]

FIRST_NAMES = [
    "ก้องภพ","พิมพ์ชนก","ธนกฤต","อรทัย","ณัฐวุฒิ","ชลธิชา","ศุภกร","กนกวรรณ","วิภาวี","ปวริศ",
    "สุเมธ","กนกพร","ภาณุ","วรพจน์","สิริกานต์","ธัญญา","ธีรภัทร","ชุติมา","นรินทร์","พัชรี",
    "จิรายุ","ณัฐชา","ภัทรพล","เบญจมาศ","ภาวินี","สิทธิชัย","อรปรียา","รวิศ","ณิชา","วรินทร"
]
LAST_NAMES = [
    "ศรีพงษ์","วัฒนชัย","แก้วกาญจน์","คำแสน","พรหมมา","อินทร์เดช","บุญช่วย","สายทอง","จันทร์เพ็ญ","นาคะ",
    "ภักดี","ศรีสุข","ชัยวัฒน์","ปรีชา","รุ่งเรือง","วีระชัย","เจริญผล","แสงทอง","ทองดี","สุวรรณ",
    "มงคล","วงศ์ทอง","สมบูรณ์","ทวีทรัพย์","ชัยสิทธิ์","สุนทร","ชาญชัย","บุญมา","ธนากร","วิเศษ"
]
COMPANY_PREFIX = ["Tech","Data","Cloud","Smart","Green","Next","Nova","Bright","Future","Mega","Spark","Cube","Mind","Hub","Prime","Siam","Metro","Blue","Rocket","Zen"]
COMPANY_SUFFIX = ["Solutions","Studio","Systems","Labs","Co., Ltd.","Group","Innovation","Digital","Network","Works"]

def pick_faculty_major():
    fac = random.choice(FACULTIES)
    maj = random.choice(MAJOR_DATA[fac])
    return fac, maj

def pick_company_name():
    return f"{random.choice(COMPANY_PREFIX)}{random.choice(COMPANY_PREFIX)} {random.choice(COMPANY_SUFFIX)}"

def pick_positions():
    return ", ".join(random.sample(POSITIONS, k=random.randint(1, 3)))

def pick_skills():
    return ", ".join(random.sample(SKILLS_POOL, k=random.randint(3, 7)))

def pick_salary():
    mode = random.choice(SALARY_MODES)
    if mode == "none":
        return "ไม่มี"
    if mode == "negotiable":
        return "ตามตกลง"
    return f"{random.choice([250, 300, 350, 400, 450, 500])} บาท"

def pick_grade():
    return None if random.random() < 0.35 else random.choice(["2.00","2.25","2.50","2.75","3.00","3.25"])

def make_dates():
    start_base = date(2026, 6, 1) + timedelta(days=random.randint(0, 40))
    end_date = start_base + timedelta(days=random.choice([90,105,120,135]))
    return f"{start_base.isoformat()} ถึง {end_date.isoformat()}"

def make_work_time():
    day = random.choice(WORK_DAYS)
    ts, te = random.choice(TIME_SLOTS)
    return f"{day} {ts} - {te}"

def unique_username(base):
    u = base
    n = 1
    while CustomUser.objects.filter(username=u).exists():
        n += 1
        u = f"{base}{n}"
    return u

def unique_email(base):
    e = base
    n = 1
    while CustomUser.objects.filter(email=e).exists():
        n += 1
        local, domain = base.split("@", 1)
        e = f"{local}{n}@{domain}"
    return e

def main():
    created_students = 0
    created_teachers = 0
    students = []
    teachers = []

    # --- students ---
    for i in range(1, N_STUDENTS + 1):
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        faculty, major = pick_faculty_major()

        username = unique_username(f"std{i:02d}_{fn.lower()}")
        email = unique_email(f"{username}@gmail.com")
        student_id = f"651{10000 + i:05d}"

        user, created = CustomUser.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": fn,
                "last_name": ln,
                "role": "student",
                "student_id": student_id,
                "faculty": faculty,
                "major": major,
                "is_active": True,
                "approved": True,
            }
        )
        if created:
            user.set_password(DEFAULT_PASSWORD)
            user.save()
            created_students += 1
        students.append(user)

    # --- teachers ---
    for i in range(1, N_TEACHERS + 1):
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        faculty, major = pick_faculty_major()

        username = unique_username(f"t{i:02d}_{fn.lower()}")
        email = unique_email(f"{username}@gmail.com")

        user, created = CustomUser.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": fn,
                "last_name": ln,
                "role": "teacher",
                "student_id": None,
                "faculty": faculty,
                "major": major,
                "is_active": True,
                "approved": True,
            }
        )
        if created:
            user.set_password(DEFAULT_PASSWORD)
            user.save()
            created_teachers += 1
        teachers.append(user)

    # --- posts ---
    owners = teachers or students or list(CustomUser.objects.all())
    created_posts = 0

    for _ in range(N_POSTS):
        owner = random.choice(owners)
        province = random.choice(PROVINCES)

        CoopPost.objects.create(
            owner=owner,
            company=pick_company_name(),
            province=province,
            salary=pick_salary(),
            position=pick_positions(),
            work_time=make_work_time(),
            internship_period=make_dates(),
            location=f"{random.choice(LOCATIONS)} ({province})",
            skills=pick_skills(),
            grade=pick_grade(),
            contact=random.choice(CONTACTS),
            type_of_work=random.choice(WORK_TYPES),
            description=random.choice(DESCRIPTIONS),
            status="approved",
        )
        created_posts += 1

    print("✅ Done!")
    print(f"Created students: {created_students}/{N_STUDENTS}")
    print(f"Created teachers: {created_teachers}/{N_TEACHERS}")
    print(f"Created posts: {created_posts}/{N_POSTS}")
    print(f"Default password: {DEFAULT_PASSWORD}")
    print("Sample users:")
    for u in (students[:2] + teachers[:2]):
        print("-", u.username, u.role, u.faculty, "/", u.major)

if __name__ == "__main__":
    main()
