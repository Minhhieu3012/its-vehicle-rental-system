import os
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import dj_database_url  # pyrefly: ignore[missing-import]
except ImportError:
    dj_database_url = None

# Định nghĩa thư mục gốc (Trỏ đến thư mục chứa manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

# 1. Thêm BASE_DIR vào hệ thống để Django nhận diện các app
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# 2. Cấu hình Bảo mật
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-^u30-jmlkmxhizxcva5*vy56kj)3beu^n%e%u!z8yfr60tv*ae',
)

# Trên Render, DEBUG sẽ là False (an toàn). Ở nhà, nó là True (để sửa lỗi).
DEBUG = 'RENDER' not in os.environ

ALLOWED_HOSTS = ['*']  # Cho phép truy cập từ mọi host trong Docker / Render

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
CSRF_TRUSTED_ORIGINS = (
    [f'https://{RENDER_EXTERNAL_HOSTNAME}'] if RENDER_EXTERNAL_HOSTNAME else []
)

# Cho phép gửi Referer hợp lệ khi gọi bản đồ OpenStreetMap / dịch vụ GIS bên ngoài
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# 3. Cấu hình Cloudinary cho Media (tự động bật khi có biến môi trường trên Render hoặc local)
CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL', '').strip()
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', '').strip()
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY', '').strip()
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', '').strip()

if CLOUDINARY_URL and not (CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET):
    parsed_cloudinary = urlparse(CLOUDINARY_URL)
    CLOUDINARY_CLOUD_NAME = parsed_cloudinary.hostname or CLOUDINARY_CLOUD_NAME
    CLOUDINARY_API_KEY = parsed_cloudinary.username or CLOUDINARY_API_KEY
    CLOUDINARY_API_SECRET = parsed_cloudinary.password or CLOUDINARY_API_SECRET

USE_CLOUDINARY = bool(CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET)

# 4. Đăng ký các ứng dụng
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

# Đặt cloudinary_storage SAU django.contrib.staticfiles để chỉ quản lý Media (giữ WhiteNoise cho Static)
if USE_CLOUDINARY:
    INSTALLED_APPS += [
        'cloudinary_storage',
        'cloudinary',
    ]

# 5. Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'vehicleRentalSystem.urls'

# 6. Cấu hình Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ROOT_DIR / 'frontend' / 'templates'],
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

# 7. Database (PostgreSQL qua Docker hoặc DATABASE_URL trên Render)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DATABASE_NAME', 'vehicle_rental_system'),
        'USER': os.environ.get('DATABASE_USER', 'postgres'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DATABASE_HOST', 'db'),
        'PORT': os.environ.get('DATABASE_PORT', '5432'),
    }
}

# Ghi đè cấu hình nếu có DATABASE_URL (Render / môi trường cloud)
if dj_database_url is not None:
    db_from_env = dj_database_url.config(conn_max_age=600)
    DATABASES['default'].update(db_from_env)

# 8. Ngôn ngữ và Thời gian
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

# 9. Static files (CSS, JS)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    ROOT_DIR / 'frontend' / 'static',
]
STATIC_ROOT = ROOT_DIR / 'staticfiles'

# 10. Media files & Storages (Django 5.1+)
MEDIA_URL = '/media/'
MEDIA_ROOT = ROOT_DIR / 'media'

if USE_CLOUDINARY:
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
        'API_KEY': CLOUDINARY_API_KEY,
        'API_SECRET': CLOUDINARY_API_SECRET,
        'SECURE': True,
    }

STORAGES = {
    'default': {
        'BACKEND': (
            'cloudinary_storage.storage.MediaCloudinaryStorage'
            if USE_CLOUDINARY
            else 'django.core.files.storage.FileSystemStorage'
        ),
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

# Giữ biến tương thích ngược cho một số gói bên thứ 3 (như django-cloudinary-storage) trên Django 5.1+
STATICFILES_STORAGE = STORAGES['staticfiles']['BACKEND']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'
