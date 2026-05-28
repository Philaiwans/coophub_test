#settings.py
from pathlib import Path 

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-your-secret-key'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'daphne',  # ต้องอยู่บรรทัดแรก
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myapp',
    'chat',  # เพิ่มตรงนี้
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'myapp.middleware.AutoExpireMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'myapp' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'coopdb',       # ตาม MYSQL_DATABASE
        'USER': 'root',
        'PASSWORD': '123456',   # ตาม MYSQL_ROOT_PASSWORD
        'HOST': '127.0.0.1',    # เพราะ Django รันบนเครื่อง Windows
        'PORT': '3306',         # ตามที่เรา -p 3306:3306
    }
}


AUTH_USER_MODEL = 'myapp.CustomUser'

LANGUAGE_CODE = 'th'
TIME_ZONE = 'Asia/Bangkok'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

# ⭐⭐ MEDIA สำคัญที่สุด ⭐⭐
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# 💌 Email Configuration (Gmail App Password)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'sopangxr@gmail.com'
EMAIL_HOST_PASSWORD = 'nxlt sqrg gvqj ptua'
DEFAULT_FROM_EMAIL = 'CoopHub <sopangxr@gmail.com>'

# ป้องกัน error timeout
EMAIL_TIMEOUT = 30

ASGI_APPLICATION = 'myproject.asgi.application'

# ใช้ in-memory สำหรับทดสอบ (ไม่ต้องติดตั้ง Redis)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}
