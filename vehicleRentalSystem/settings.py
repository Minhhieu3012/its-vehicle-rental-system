"""
Django settings for vehicleRentalSystem project.
FILE ĐÃ MERGE: Hỗ trợ cả Map, Frontend, Review và Upload ảnh.
"""

from pathlib import Path
import os

# 1. Định nghĩa thư mục gốc
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Cấu hình Bảo mật
SECRET_KEY = 'django-insecure-^u30-jmlkmxhizxcva5*vy56kj)3beu^n%e%u!z8yfr60tv*ae'
DEBUG = True
ALLOWED_HOSTS = []

# 3. Đăng ký các ứng dụng (Apps) - GỘP CẢ 2 NHÁNH
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Các App chức năng
    'users',      # Quản lý User
    'bookings',   # Quản lý Đặt xe
    'vehicles',   # Quản lý Xe & Map
   
    
    # App Giao diện (Lấy từ nhánh Frontend)
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

# 5. Cấu hình Templates (Ưu tiên cấu hình của Frontend)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'frontend' / 'templates'], # Trỏ về thư mục chứa giao diện đẹp
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
        'HOST': 'db', # Tên service trong docker-compose
        'PORT': 5432,
    }
}

# 7. Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# 8. Ngôn ngữ và Thời gian (Ưu tiên Tiếng Việt)
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

# 9. Static files (CSS, JS, Images)
STATIC_URL = 'static/'
# Thêm đường dẫn Static của Frontend vào để Django tìm thấy file CSS/JS
STATICFILES_DIRS = [
    BASE_DIR / "frontend" / "static", 
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# 10. Media files (Upload ảnh xe)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 11. Cấu hình User Model & ID
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'