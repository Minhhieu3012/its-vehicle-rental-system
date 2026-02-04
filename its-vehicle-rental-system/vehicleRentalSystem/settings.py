"""
Django settings for vehicleRentalSystem project.
Bản sửa lỗi: Khớp cấu trúc thư mục lồng nhau thực tế.
"""

from pathlib import Path
import os

# 1. Định nghĩa thư mục gốc (Trỏ đến thư mục chứa manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Cấu hình Bảo mật
SECRET_KEY = 'django-insecure-^u30-jmlkmxhizxcva5*vy56kj)3beu^n%e%u!z8yfr60tv*ae'
DEBUG = True
ALLOWED_HOSTS = ['*'] # Cho phép truy cập từ mọi host trong Docker

# 3. Đăng ký các ứng dụng
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'users',      
    'bookings',   
    'vehicles',   
    'reviews',   
    'frontend',   
]

# 4. Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'vehicleRentalSystem.urls'

# 5. Cấu hình Templates (ĐÃ SỬA: Thêm folder bọc ngoài)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR  / 'frontend' / 'templates'], # Khớp với image_1ab828.png
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

WSGI_APPLICATION = 'vehicleRentalSystem.wsgi.application'

# 6. Database (PostgreSQL qua Docker)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'vehicle_rental_system',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'db',
        'PORT': 5432,
    }
}

# 8. Ngôn ngữ và Thời gian
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

# 9. Static files (CSS, JS) - ĐÃ SỬA: Thêm folder bọc ngoài
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / "frontend" / "static", # Khớp với image_1ab828.png
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# 10. Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'