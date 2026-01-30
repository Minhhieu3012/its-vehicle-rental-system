from django import forms
from django.contrib.auth.models import User
# Giả sử bạn đã định nghĩa model Review trong models.py
# from .models import Review

class RegistrationForm(forms.ModelForm):
    # Khai báo thêm trường mật khẩu và xác nhận mật khẩu
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full pl-11 pr-4 py-3 rounded-lg border border-[#cfd7e7] bg-white text-[#0d121b]',
        'placeholder': 'Nhập ít nhất 8 ký tự'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full pl-11 pr-4 py-3 rounded-lg border border-[#cfd7e7] bg-white text-[#0d121b]',
        'placeholder': 'Nhập lại mật khẩu'
    }))
    
    # Trường tải lên GPLX
    gplx_image = forms.ImageField(required=True)

    class Meta:
        model = User
        fields = ['username', 'password']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full pl-11 pr-4 py-3 rounded-lg border border-[#cfd7e7] bg-white text-[#0d121b]',
                'placeholder': 'Nhập tên đăng nhập của bạn'
            }),
        }

    # Logic kiểm tra mật khẩu khớp nhau
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise forms.ValidationError("Mật khẩu xác nhận không khớp.")

class ReviewForm(forms.Form):
    rating = forms.IntegerField(min_value=1, max_value=5)
    comment = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'w-full rounded-lg border-[#cfd7e7] bg-background-light text-[#0d121b]',
        'placeholder': 'Kể cho chúng tôi về trải nghiệm lái, sự tiện nghi...',
        'rows': '4'
    }))