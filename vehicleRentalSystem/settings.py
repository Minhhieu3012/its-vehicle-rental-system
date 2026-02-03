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
    'reviews',   # Quản lý Đánh giá
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
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

# 10. Media files (Upload ảnh xe)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 11. Cấu hình User Model & ID
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'

# 1. Nếu người dùng chưa đăng nhập mà cố vào trang kín -> Đá về trang này
LOGIN_URL = 'frontend:login'

# 2. Đăng nhập xong -> Chuyển hướng về Trang chủ (hoặc Map tùy bạn thích)
LOGIN_REDIRECT_URL = 'frontend:home'  
# Hoặc nếu muốn vào map luôn: LOGIN_REDIRECT_URL = 'vehicles:map'

# 3. Đăng xuất xong -> Chuyển hướng về trang Đăng nhập (FIX LỖI CỦA BẠN Ở ĐÂY)
LOGOUT_REDIRECT_URL = 'frontend:login'