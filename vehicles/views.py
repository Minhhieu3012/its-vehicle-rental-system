from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET

from .models import Vehicle, Review, VehicleImage
from .forms import ReviewForm, VehicleImageForm, MultipleImageUploadForm


# ============== API ENDPOINTS ==============

@require_GET
def vehicle_list_api(request):
    """API: Lấy danh sách xe với bộ lọc và sắp xếp"""
    vehicles = Vehicle.objects.annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )
    
    # Lọc theo trạng thái
    availability = request.GET.get('availability')
    if availability == 'available':
        vehicles = vehicles.filter(is_available=True)
    elif availability == 'unavailable':
        vehicles = vehicles.filter(is_available=False)
    
    # Lọc theo giá
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        vehicles = vehicles.filter(price_per_day__gte=min_price)
    if max_price:
        vehicles = vehicles.filter(price_per_day__lte=max_price)
    
    # Sắp xếp
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_asc':
        vehicles = vehicles.order_by('price_per_day')
    elif sort_by == 'price_desc':
        vehicles = vehicles.order_by('-price_per_day')
    elif sort_by == 'rating':
        vehicles = vehicles.order_by('-avg_rating')
    else:
        vehicles = vehicles.order_by('name')
    
    # Phân trang
    page = request.GET.get('page', 1)
    paginator = Paginator(vehicles, 9)
    page_obj = paginator.get_page(page)
    
    data = {
        'vehicles': [
            {
                'id': v.id,
                'name': v.name,
                'price_per_day': float(v.price_per_day),
                'image': v.image.url if v.image else None,
                'is_available': v.is_available,
                'avg_rating': round(v.avg_rating, 1) if v.avg_rating else None,
                'review_count': v.review_count,
            }
            for v in page_obj
        ],
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    }
    return JsonResponse(data)


@require_GET
def vehicle_detail_api(request, pk):
    """API: Lấy chi tiết xe, ảnh và đánh giá"""
    vehicle = get_object_or_404(
        Vehicle.objects.annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        ),
        pk=pk
    )
    
    # Lấy tất cả ảnh của xe
    images = vehicle.images.all()
    
    # Lấy tất cả đánh giá
    reviews = vehicle.reviews.select_related('user').order_by('-created_at')
    
    data = {
        'vehicle': {
            'id': vehicle.id,
            'name': vehicle.name,
            'price_per_day': float(vehicle.price_per_day),
            'image': vehicle.image.url if vehicle.image else None,
            'is_available': vehicle.is_available,
            'avg_rating': round(vehicle.avg_rating, 1) if vehicle.avg_rating else None,
            'review_count': vehicle.review_count,
        },
        'images': [
            {'id': img.id, 'url': img.image.url}
            for img in images
        ],
        'reviews': [
            {
                'id': r.id,
                'user': r.user.username,
                'rating': r.rating,
                'comment': r.comment,
                'created_at': r.created_at.isoformat(),
            }
            for r in reviews
        ]
    }
    return JsonResponse(data)


@login_required
def add_review(request, vehicle_pk):
    """API: Thêm hoặc cập nhật đánh giá cho xe"""
    vehicle = get_object_or_404(Vehicle, pk=vehicle_pk)
    
    # Kiểm tra xem user đã đánh giá xe này chưa
    existing_review = Review.objects.filter(vehicle=vehicle, user=request.user).first()
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.vehicle = vehicle
            review.user = request.user
            review.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Đã cập nhật đánh giá!' if existing_review else 'Cảm ơn bạn đã đánh giá!',
                'review': {
                    'id': review.id,
                    'rating': review.rating,
                    'comment': review.comment,
                    'created_at': review.created_at.isoformat(),
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
    
    # GET: Trả về thông tin review hiện tại (nếu có)
    if existing_review:
        return JsonResponse({
            'has_review': True,
            'review': {
                'id': existing_review.id,
                'rating': existing_review.rating,
                'comment': existing_review.comment,
            }
        })
    return JsonResponse({'has_review': False})


@login_required
@require_POST
def delete_review(request, review_pk):
    """API: Xóa đánh giá của user"""
    review = get_object_or_404(Review, pk=review_pk, user=request.user)
    vehicle_pk = review.vehicle.pk
    review.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Đã xóa đánh giá!',
        'vehicle_id': vehicle_pk
    })


@login_required
def upload_images(request, vehicle_pk):
    """API: Upload nhiều ảnh cho xe"""
    vehicle = get_object_or_404(Vehicle, pk=vehicle_pk)
    
    if request.method == 'POST':
        images = request.FILES.getlist('images')
        
        if not images:
            return JsonResponse({
                'success': False,
                'message': 'Không có ảnh nào được chọn.'
            }, status=400)
        
        uploaded = []
        errors = []
        
        for image in images:
            # Kiểm tra dung lượng (max 5MB)
            if image.size > 5 * 1024 * 1024:
                errors.append(f'{image.name}: Vượt quá 5MB')
                continue
            
            # Kiểm tra định dạng
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if image.content_type not in allowed_types:
                errors.append(f'{image.name}: Định dạng không hỗ trợ')
                continue
            
            # Lưu ảnh
            vehicle_image = VehicleImage.objects.create(vehicle=vehicle, image=image)
            uploaded.append({
                'id': vehicle_image.id,
                'url': vehicle_image.image.url
            })
        
        return JsonResponse({
            'success': True,
            'message': f'Đã upload {len(uploaded)} ảnh thành công!',
            'uploaded': uploaded,
            'errors': errors if errors else None
        })
    
    # GET: Trả về danh sách ảnh hiện tại
    images = vehicle.images.all()
    return JsonResponse({
        'vehicle_id': vehicle.pk,
        'vehicle_name': vehicle.name,
        'images': [
            {'id': img.id, 'url': img.image.url}
            for img in images
        ]
    })


@login_required
@require_POST
def delete_image(request, image_pk):
    """API: Xóa một ảnh của xe (chỉ staff)"""
    image = get_object_or_404(VehicleImage, pk=image_pk)
    vehicle_pk = image.vehicle.pk
    
    # Chỉ staff mới được xóa ảnh
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Bạn không có quyền xóa ảnh này.'
        }, status=403)
    
    image.image.delete()  # Xóa file thực tế
    image.delete()
    
    return JsonResponse({
        'success': True,
        'message': 'Đã xóa ảnh!',
        'vehicle_id': vehicle_pk
    })


@require_GET
def get_vehicle_rating(request, vehicle_pk):
    """API: Lấy thông tin rating của xe"""
    vehicle = get_object_or_404(Vehicle, pk=vehicle_pk)
    
    stats = vehicle.reviews.aggregate(
        avg_rating=Avg('rating'),
        review_count=Count('id')
    )
    
    # Phân bố rating
    rating_distribution = {}
    for i in range(1, 6):
        count = vehicle.reviews.filter(rating=i).count()
        rating_distribution[str(i)] = count
    
    return JsonResponse({
        'vehicle_id': vehicle.pk,
        'avg_rating': round(stats['avg_rating'], 1) if stats['avg_rating'] else 0,
        'review_count': stats['review_count'],
        'rating_distribution': rating_distribution,
    })
