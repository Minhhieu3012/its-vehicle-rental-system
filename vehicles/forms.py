from django import forms
from .models import Review, VehicleImage, Vehicle


class ReviewForm(forms.ModelForm):
    """Form để người dùng đánh giá xe"""
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(attrs={'class': 'rating-radio'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Nhập nhận xét của bạn về xe này...'
            }),
        }
        labels = {
            'rating': 'Đánh giá',
            'comment': 'Nhận xét',
        }


class VehicleImageForm(forms.ModelForm):
    """Form để upload ảnh xe"""
    class Meta:
        model = VehicleImage
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        labels = {
            'image': 'Chọn ảnh',
        }


class MultipleFileInput(forms.ClearableFileInput):
    """Custom widget để hỗ trợ upload nhiều file"""
    allow_multiple_selected = True


class MultipleImageUploadForm(forms.Form):
    """Form để upload nhiều ảnh cùng lúc"""
    images = forms.ImageField(
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        label='Chọn ảnh (có thể chọn nhiều ảnh)',
        required=False
    )

    def clean_images(self):
        """Validate ảnh được upload - không dùng vì xử lý trong view"""
        return self.cleaned_data.get('images')


class VehicleForm(forms.ModelForm):
    """Form để tạo/sửa xe"""
    class Meta:
        model = Vehicle
        fields = ['name', 'price_per_day', 'image', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập tên xe'
            }),
            'price_per_day': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập giá thuê/ngày'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
