from django import forms
from users.models import User

class RegisterForm(forms.ModelForm):
    # Định nghĩa các trường mật khẩu với kiểu input password
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Nhập mật khẩu'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Xác nhận mật khẩu'
    }))

    class Meta:
        model = User
        # Các trường này lấy trực tiếp từ Model User của Bảo
        fields = ['username', 'email', 'phone_number', 'address', 'driver_license_image', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tên đăng nhập'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Số điện thoại'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Địa chỉ'}),
            'driver_license_image': forms.FileInput(attrs={'class': 'form-control-file'}),
        }

    # Logic kiểm tra mật khẩu trùng khớp
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Mật khẩu xác nhận không khớp!")
        return cleaned_data